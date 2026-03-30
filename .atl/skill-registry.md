# Skill Registry — documentor

Generated: 2026-03-30

## User Skills

| Skill | Source | Trigger |
|-------|--------|---------|
| deslop | ~/.claude/skills/deslop | Check diff against dev, remove AI slop |
| code-review | ~/.claude/skills/code-review | `/code-review [staged | pr <n> | commit <hash> | files <path>]` |
| go-testing | ~/.claude/skills/go-testing | Writing Go tests, using teatest, adding test coverage |
| branch-pr | ~/.claude/skills/branch-pr | Creating a pull request, opening a PR |
| issue-creation | ~/.claude/skills/issue-creation | Creating a GitHub issue, reporting a bug, requesting a feature |
| judgment-day | ~/.claude/skills/judgment-day | "judgment day", "dual review", "doble review", "juzgar" |
| skill-creator | ~/.claude/skills/skill-creator | Create a new skill, add agent instructions, document patterns |
| session-summary | ~/.claude/skills/session-summary | Generate session summary for new context |

## Project Conventions

| File | Source | Purpose |
|------|--------|---------|
| CLAUDE.md | project root | Project architecture, coding conventions, testing rules, hex arch dependency rules |

## Compact Rules

### From CLAUDE.md (project)
- Hexagonal Architecture: domain → application → infrastructure → adapters (strict dependency direction)
- DDD: Entities have identity, Value Objects are frozen dataclasses, Repos are ports in domain
- UnitOfWork pattern: repos use flush(), commit() is explicit in use cases
- Python 3.13+, type hints always, no `Any` unless justified
- FastAPI: app factory + lifespan, schemas separate from DTOs, DI via Depends()
- Testing: pytest + pytest-asyncio, naming `test_{action}_should_{result}_when_{condition}`
- Package manager: uv (not pip, not poetry)
- Conventional commits in English, no AI attribution
- YAGNI: don't implement unasked features, don't over-abstract

### From code-review
- Reviews: security, performance, reliability, architecture, quality
- Targets: staged, PR number, commit hash, or file paths

### From branch-pr
- Issue-first enforcement: PRs link to issues
- Follow project PR conventions

### From issue-creation
- Issue-first enforcement: create issues before PRs
- Bug reports and feature requests
