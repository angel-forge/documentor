# 006 — Multi-Language Full-Text Search

Date: 2026-03-30

## Context

The hybrid search implementation (ADR 005) hardcoded `english` as the PostgreSQL FTS configuration for both the `search_vector` stored generated column and query-time `plainto_tsquery`. The system will be used for end-user application documentation — not just technical docs — in multiple languages. English stemming applied to Spanish or French text degrades FTS quality significantly ("configuración" won't match "configurar", "usuarios" won't match "usuario").

## Decision

Add a `language` field to `Document` and `Chunk` entities. Replace the stored generated column with a trigger-maintained `tsvector` column that uses the per-row language for correct stemming.

## How It Works

### Language flow

```
User specifies language at ingestion (default: "english")
  → Document.language validated against SUPPORTED_FTS_LANGUAGES (23 configs)
  → Each Chunk inherits document.language (denormalized)
  → PostgreSQL trigger computes: to_tsvector(NEW.language::regconfig, NEW.text)
  → Query-time: plainto_tsquery(settings.search_language, query_text)
```

### Trigger vs generated column

PostgreSQL stored generated columns cannot reference other column values dynamically — `GENERATED ALWAYS AS (to_tsvector(language::regconfig, text))` is not supported. A `BEFORE INSERT OR UPDATE` trigger is the standard PostgreSQL pattern for this.

### Supported languages

23 PostgreSQL built-in FTS configurations defined as a `frozenset` in the domain layer:

`simple`, `arabic`, `danish`, `dutch`, `english`, `finnish`, `french`, `german`, `greek`, `hungarian`, `indonesian`, `irish`, `italian`, `lithuanian`, `nepali`, `norwegian`, `portuguese`, `romanian`, `russian`, `spanish`, `swedish`, `tamil`, `turkish`

### Validation

Dual validation for fast feedback:
- **Adapter layer**: Pydantic `field_validator` normalizes to lowercase and rejects unknown values (HTTP 422).
- **Domain layer**: `Document.__post_init__` validates against the frozenset and raises `InvalidDocumentError`.

## Key Decisions

### Language per document, not per chunk

Documentation for a product is written in one language. A document won't be half Spanish, half German. Per-document granularity is sufficient and simpler than per-chunk.

### Hardcoded allowlist, not runtime catalog

The domain layer cannot query the database to discover available FTS configurations. A hardcoded `frozenset` of the 23 built-in PostgreSQL FTS configs keeps the domain clean. The set is effectively static — PostgreSQL rarely adds new built-in configs.

### Query-time language stays global

`plainto_tsquery` at search time uses `settings.search_language`, not per-chunk language. Grouping chunks by language, running separate tsqueries, and merging would add complexity for minimal gain — vector search via RRF compensates for any FTS mismatch.

### No automatic language detection (yet)

The user specifies the language at ingestion time. Auto-detection (via `langdetect` or `lingua`) is a future enhancement. Detection is reliable on full documents (long text) but fragile on short chunks or mixed-language technical content.

## Migration

Alembic migration 005:
1. Add `language VARCHAR NOT NULL DEFAULT 'english'` to both `documents` and `chunks` tables
2. Drop the generated `search_vector` column
3. Add plain `search_vector tsvector` column
4. Create trigger function and trigger
5. Backfill existing rows with `to_tsvector('english'::regconfig, text)`
6. Recreate GIN index

Fully reversible — downgrade restores the generated column.

## Consequences

- Existing documents get `language = 'english'` via the default. No data loss, no behavioral change for existing content.
- Adding a new language requires only adding it to the `SUPPORTED_FTS_LANGUAGES` frozenset — no migration needed.
- Trigger adds negligible overhead vs generated column (standard PostgreSQL pattern).
- If `search_language` diverges from a document's actual language, FTS results degrade for that document. Vector search compensates via RRF.
