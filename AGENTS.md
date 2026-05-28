# Code Review Rules — backend-qolqa

## Architecture

This project follows **Clean Architecture** with strict layer separation:

```
domain/          ← Pure business logic. Zero infrastructure imports.
application/     ← Use cases and DTOs. Depends only on domain.
infrastructure/  ← MongoDB, JWT, mappers, password hashing.
api/             ← FastAPI controllers and dependencies. Depends on application + infrastructure.
config/          ← Settings and DB clients.
scripts/         ← Standalone maintenance/migration scripts.
```

### Layer rules
- `domain/` must never import from `infrastructure/`, `api/`, or `application/`.
- `application/` must never import from `infrastructure/` or `api/`.
- `infrastructure/` may import from `domain/` and `application/dtos/`.
- `api/` may import from all layers but must not contain business logic.
- Domain errors (`Missing`, `Duplicate`) must be raised in repositories, never `HTTPException`.
- `HTTPException` belongs only in `api/` controllers and dependencies.

## Python

- Python 3.10+ syntax (`str | int`, `match`, etc.) is allowed.
- Use `Optional[T]` or `T | None` consistently — do not mix within the same file.
- All public functions must have type annotations.
- Use `async/await` for all I/O operations — no synchronous DB or HTTP calls.
- No bare `except:` — always catch specific exceptions or at minimum `Exception as exc`.
- Never expose `hashed_password` or raw MongoDB `_id` in API responses.

## FastAPI

- Routers live in `api/controllers/`. One file per domain area.
- Shared FastAPI `Depends` live in `api/dependencies/`. Never define reusable deps inside controllers.
- Use `response_model=` on every endpoint — no untyped responses.
- Use `status.HTTP_*` constants — never hardcode status codes as integers.
- Rate limiting with `slowapi` must be applied to auth endpoints (`/register`, `/login`).
- All endpoints must delegate errors to `handle_common_errors` — no raw `raise HTTPException` for domain errors.

## Pydantic

- DTOs live in `application/dtos/`. Separate files per domain area.
- Response DTOs (e.g. `UserResponse`) must never include password fields.
- Use `model_dump(exclude_unset=True)` for partial updates — never overwrite fields with `None` unintentionally.
- `field_validator` for input sanitization (username lowercase, password strength) must live in the DTO, not the controller.
- `AdminUserUpdateRequest` and `UserUpdateRequest` must remain separate — never merge them. This prevents privilege escalation.

## MongoDB / Motor

- All DB operations go through `IUserRepository` implementations — no direct collection access in controllers.
- Exception: `$inc` for `token_version` in admin controller is acceptable as a targeted atomic operation.
- Use `ObjectId.is_valid()` before constructing `ObjectId` — raise `Missing` if invalid.
- Mappers (`infrastructure/mappers/`) handle all raw dict ↔ entity conversions. No inline mapping in repositories or controllers.

## Security

- JWT tokens must include `roles` and `token_version` in the payload.
- `get_current_user` must validate `token_version` against the DB value on every request.
- `require_admin` reads roles from the JWT payload — it must not make an extra DB query.
- When `roles` change on a user, `token_version` must be incremented atomically (`$inc`) to invalidate existing tokens.
- `UserUpdateRequest` (self-service) must never accept `roles` or `token_version` fields.
- The `promote` endpoint (`POST /admin/users/{id}/promote`) must be idempotent — if user is already admin, return current state without side effects.

## Naming conventions

- Controllers: `api/controllers/<domain>.py` (e.g. `user.py`, `admin.py`, `auth.py`)
- Repositories: `infrastructure/repositories/<Domain>RepoImpl.py`
- Mappers: `infrastructure/mappers/<Domain>Mapper.py`
- DTOs: `application/dtos/<domain>/AuthRequest.py`, `AuthResponse.py`
- Use cases: `application/use_cases/<domain>/<ActionName>.py` (PascalCase filename)
- Domain entities: `domain/entities/<domain>/<Name>Entity.py`
- Domain enums: `domain/enums/<Name>.py`

## Testing

- Tests use **pytest** with async support (`pytest-asyncio`).
- Test files mirror the source tree: `tests/api/controllers/test_user.py` mirrors `api/controllers/user.py`.
- Use `TestClient` or `AsyncClient` from `httpx` for endpoint tests — no direct function calls in integration tests.
- Every new endpoint needs at least: happy path, unauthorized (401), and forbidden (403) test cases.
- Admin endpoints must have a test that verifies a non-admin user receives 403.
- Mock DB at the repository level using `unittest.mock.AsyncMock` — never mock at the Motor level.

## Migration scripts

- Scripts live in `scripts/` and are standalone Python files runnable with `python3 scripts/<name>.py`.
- Must support a `--dry-run` flag that prints affected documents without writing.
- Must print a summary of modified document counts after execution.
- Must close the DB client before exiting.

## Commits

- Use Conventional Commits: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`.
- Scope in parentheses matches the domain area: `feat(users)`, `fix(auth)`, `refactor(admin)`.
- One work unit per commit — do not bundle domain changes with controller changes.
- Never commit secrets, `.env` files, or `__pycache__/`.

## Skills available for this project

The following AI skills are installed and should be applied when relevant:

| Skill | When to apply |
|-------|---------------|
| `pytest` | Writing or reviewing Python tests |
| `fastapi-python` (mindrally) | FastAPI endpoint patterns, dependency injection |
| `pydantic` (bobmatnyc) | Pydantic model design, validators, serialization |
| `sqlalchemy` (bobmatnyc) | SQLAlchemy models and queries (if SQL path is used) |
| `sqlalchemy-alembic-expert-best-practices-code-review` (wispbit-ai) | Alembic migration review |
| `python-testing-patterns` (wshobson) | Pytest fixtures, mocking, async test patterns |
| `fastapi-templates` (wshobson) | FastAPI project structure templates |
| `work-unit-commits` | Commit splitting, chained PRs, reviewable work units |
| `cognitive-doc-design` | Writing READMEs, architecture docs, onboarding guides |
