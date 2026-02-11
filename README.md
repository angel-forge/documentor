# DocuMentor

Asistente de estudio sobre documentación técnica pública que usa RAG (Retrieval-Augmented Generation) para responder preguntas precisas con referencias a la fuente.

**Stack:** Python 3.13+ / FastAPI / PostgreSQL + pgvector / Anthropic Claude & OpenAI / uv

## Prerrequisitos

- [Python 3.13+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/) — package manager
- [Docker](https://www.docker.com/) — para la base de datos

## Inicio rápido

```bash
# 1. Instalar dependencias
uv sync

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys

# 3. Levantar la base de datos
make up

# 4. Ejecutar migraciones
make migrate
```

Para verificar que todo funciona:

```bash
# Ver las tablas creadas
docker compose exec db psql -U documentor -d documentor -c '\dt'

# Ver la extensión pgvector
docker compose exec db psql -U documentor -d documentor -c '\dx'
```

## Conexión desde TablePlus

```
postgresql://documentor:documentor@localhost:5432/documentor
```

## Comandos disponibles

| Comando          | Descripción                                      |
|------------------|--------------------------------------------------|
| `make up`        | Levanta el contenedor de PostgreSQL               |
| `make down`      | Detiene el contenedor                             |
| `make migrate`   | Ejecuta las migraciones de Alembic                |
| `make reset-db`  | Destruye la BD, recrea y migra desde cero         |
| `make lint`      | Ejecuta el linter (ruff check)                    |
| `make format`    | Formatea el código (ruff format)                  |
| `make test`      | Ejecuta tests unitarios                           |
| `make test-int`  | Ejecuta tests de integración (necesita Docker)    |
| `make test-all`  | Ejecuta todos los tests con cobertura             |
| `make help`      | Muestra todos los comandos disponibles            |

## Tests

```bash
make test          # Unit tests — rápidos, sin dependencias externas
make test-int      # Integration tests — usa testcontainers (Docker)
make test-all      # Todos los tests con reporte de cobertura
```

## Arquitectura

Hexagonal (Ports & Adapters) + DDD:

```
src/documentor/
├── domain/            # Entidades, Value Objects, puertos (interfaces)
├── application/       # Casos de uso y DTOs
├── infrastructure/    # Implementaciones: PostgreSQL, OpenAI, Anthropic
└── adapters/          # API FastAPI (próximamente)
```

**Reglas de dependencia:** `domain` no importa de nadie. `application` solo de `domain`. `infrastructure` implementa los puertos de `domain`. `adapters` conecta todo.
