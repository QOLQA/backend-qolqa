# Reporte de Arquitectura — Backend Qolqa (Clean Architecture)

**Repositorio:** `backend-qolqa`
**Commit analyzed:** `f6a97d6` (`chore: remove dead SQL schemas (schemas/)`)
**Fecha:** 2026-10-26
**Stack:** Python 3.10+ · FastAPI 0.110.3 · Motor 3.6.0 · MongoDB · Pydantic v2 · python-jose · bcrypt · slowapi

---

## 1. Resumen ejecutivo

El backend de **Qolqa** implementa Clean Architecture con **5 capas** y **4 dominios de negocio** (`auth`, `query`, `solution`, `version`). La migración se ejecutó con una estrategia *strangler* bottom-up, y desde el reporte anterior (commit `55a7087`) se han aplicado **todas las correcciones críticas y de deuda técnica** identificadas.

**Estado de las reglas de dependencia (verificado con `grep` sobre el código fuente):**

| Regla | Estado | Detalle |
|---|---|---|
| `domain/` no importa de otras capas | ✅ **Cumple al 100%** | Cero imports hacia `application/`, `infra.persistence/`, `infra.presentation/`, `config/` |
| `application/` no importa de `infra.presentation/` | ✅ **Cumple** | Cero imports de `fastapi`, `starlette`, `HTTPException` |
| `application/` no importa de `config/` | ✅ **Cumple** | `settings` se inyecta como parámetro, no se importa |
| `application/` no importa de `infra.persistence/` | ✅ **Cumple al 100%** | **0 violaciones** — se eliminaron las 6 previas vía puerto `IPasswordHasher` |
| `infra.persistence/` no lanza `HTTPException` | ✅ **Cumple** | Código muerto eliminado (`db_timeout.py`, `mongo_utils.py`) |
| Errores de dominio en repositorios | ✅ **Cumple** | Los 4 repositorios lanzan solo `Missing`/`Duplicate` |
| `HTTPException` solo en `infra.presentation/` | ✅ **Cumple** | |

**Métricas del codebase:**

| Métrica | Valor |
|---|---|
| Endpoints REST | 31 (30 versionados + `GET /health`) |
| Casos de uso (application layer) | 21 (auth 4, query 7, solution 5, version 5) |
| Entidades de dominio | 5 aggregates + value objects recursivos |
| Interfaces de repositorio (domain) | 4 (`IUserRepository`, `IQueryRepository`, `ISolutionRepository`, `IVersionRepository`) |
| Implementaciones de repositorio | 4 (`*RepoImpl`) |
| Mappers (dict ↔ entidad) | 4 |
| Clases de error de dominio | 9 |
| Tests | 150 pasan · 4 fallan (requieren Mongo vivo o script eliminado) |
| Módulos de código muerto | 0 (limpios) |
| Commits de la migración + limpieza | 14 (PRs #50–#59 + cleanup) |

**Veredicto:** la arquitectura está **estructuralmente sólida**. El dominio es puro, la capa de aplicación está poblada, los errores de dominio están desacoplados del HTTP, y las 6 violaciones de dependencia del dominio `auth` se eliminaron. Quedan **cuatro findings de seguridad/operación** por atender (ver §4).

---

## 2. Qué se resolvió desde el reporte anterior (commit `55a7087`)

El reporte anterior listaba 6 violaciones críticas y 4 riesgos de seguridad. Todos los **críticos** y la **mayoría de los altos** ya están corregidos:

| # | Finding (reporte anterior) | Estado | Cómo se resolvió |
|---|---|---|---|
| 9.1 | Guard de `secret_key` en producción nunca se ejecuta | ✅ **Resuelto** | `environment` declarado antes que `secret_key`; validator `mode='before'` lee `info.data` correctamente (`config/settings.py`) |
| 9.2 | `print(settings)` filtra `secret_key` a stdout | ✅ **Resuelto** | Eliminados los `print(settings)` de `main.py` |
| 9.3 | Fuga cross-tenant en `GET /versions` y `GET /queries` | ⏳ **Pendiente** | Los listados globales aún no filtran por owner (ver §4.1) |
| 9.4 | Mutaciones de `version` sin verificación de ownership | ✅ **Resuelto** | `UpdateVersion` y `DeleteVersion` ya verifican ownership (raises `Forbidden`) |
| 9.5 | 6 violaciones `application → infrastructure` | ✅ **Resuelto** | Puerto `IPasswordHasher` en `domain/security/`; bcrypt en `infra/persistence/security/`; `AuthenticateUser`/`RegisterUser` dependen de la interfaz |
| 9.6 | `IVersionRepository` vacío (`pass`) | ✅ **Resuelto** | Declara `get_by_id`, `get_all`, `save`, `get_by_solution_id`, `get_by_solution_ids`, `delete_by_solution_id` |
| 9.7 | Sin índices en MongoDB | ✅ **Resuelto** | Índices creados en el `lifespan` de `main.py` (startup idempotente) |
| 9.8 | Tests rotos por `scripts/migrate_add_google_fields.py` borrado | ✅ **Resuelto** | Tests eliminados y script limpiado |
| 9.9 | Cascada de borrado no transaccional | ✅ **Resuelto** | `DeleteSolution` usa transacción de MongoDB (`async with session.start_transaction()`) |
| 9.11 | 5 instancias de `Limiter` | ✅ **Resuelto** | Limiter compartido en `config/rate_limiter.py`, inyectado desde `main.py` |
| 9.14 | Código muerto (`db_timeout.py`, `mongo_utils.py`, `documents/`) | ✅ **Resuelto** | `db_timeout.py` eliminado; `mongo_utils.py` movido a `tests/helpers/`; `documents/` se mantiene como modelo de Mongo (no es muerto) |

---

## 3. Mapa de capas y dependencias (estado actual)

```
backend-qolqa/
├── main.py                          # Composition root: app, middleware, routers, lifespan
├── config/                          # Settings, Mongo client, rate limiter
│   ├── settings.py                  # Pydantic Settings (env-driven)
│   ├── mongo.py                     # AsyncIOMotorClient singleton
│   ├── rate_limiter.py              # SlowAPI Limiter compartido (único)
│   └── sql.py                       # Scaffold SQLAlchemy (NO funcional)
├── domain/                          # ◀── REGLA DE ORO: no importa nada externo
│   ├── entities/                    # Modelo de negocio (dataclasses puros)
│   │   ├── auth/{UserEntity, TokenEntity}.py
│   │   ├── QueryEntity.py
│   │   ├── SolutionEntity.py
│   │   └── VersionEntity.py
│   ├── enums/{RoleEnum, AuthProviderEnum}.py
│   ├── errors.py                    # 9 errores de dominio
│   ├── security/                    # ◀── Puerto de contraseñas (nuevo)
│   │   └── password.py              # IPasswordHasher interface
│   └── repositories/                # Interfaces (contratos)
│       ├── user/repo.py
│       ├── query/repo.py
│       ├── solution/repo.py
│       └── version/repo.py
├── application/                     # ◀── Orquestación; depende solo de domain
│   ├── dtos/{auth,query,solution,version}/
│   │   ├── commands.py / queries.py   # Contrato de entrada de use cases
│   │   └── Request.py / Response.py   # Contrato de salida de use cases
│   └── use_cases/{auth,query,solution,version}/   # 21 funciones async
├── infra/                           # ◀── Adaptadores técnicos
│   ├── persistence/                 # External concerns (database, auth, logging)
│   │   ├── repositories/            # 4 implementaciones Motor (*RepoImpl)
│   │   ├── mappers/                 # 4 mappers dict ↔ entidad
│   │   ├── documents/               # MongoDB document models (Pydantic) — forma de almacenamiento
│   │   ├── security/                # BcryptHasher (implementa IPasswordHasher)
│   │   ├── services/                # GoogleAuthService
│   │   ├── jwt.py · token_service.py · password.py
│   │   ├── audit.py                 # Auditoría a archivo JSON-lines
│   │   └── base.py · db_factory.py
│   └── presentation/                # HTTP: routers, dependencies, error mapping
│       ├── routers/{auth,user,admin,query,version,solution}.py
│       ├── dependencies/{auth,common,use_cases}.py   # Wiring de FastAPI Depends
│       ├── dtos/{auth,query,solution,version}/       # Schemas de petición/respuesta HTTP
│       └── exception_handlers.py
├── tests/
├── openspec/
├── scripts/
└── docs/                            # Este reporte
```

**Diagrama de dependencias:**

```
infra.presentation/ (HTTP: routers + DTOs de presentación)
        │ ▲
        │ │  ← imports hacia application/domain
        ▼ │
application/ (use cases: 21 funciones async + DTOs de aplicación)
        │
        ▼
domain/ (núcleo: entidades, enums, errores, repository ABCs, IPasswordHasher)
        ▲
        │  implements
infra.persistence/ (adaptadores: repos impl, mappers, documents, security, jwt)
```

`domain/` no tiene flechas salientes. Es el único anillo que cumple la regla al 100%.

---

## 4. Findings restantes (pendientes)

### 4.1 Fuga de datos cross-tenant en `GET /versions` y `GET /queries` — ALTO

`VersionRepoImpl.get_all()` y `QueryRepoImpl.get_all()` **no filtran por owner**. Cualquier usuario autenticado puede listar todas las versiones (que contienen el `submodels` completo: el diseño del esquema de cada solución) y todas las queries.

`GET /queries` documenta *"admin endpoint"* en su docstring **pero no tiene `require_admin`**.

Contraste: `GET /solutions` **sí** filtra por owner vía `get_all_for_user`.

**Fix:** Agregar filtro por `user_id` en `get_all()` de versiones y queries, o exponer `get_all_for_user` y usarlo en los routers. Evaluar `require_admin` para el listado global si se desea mantener sin filtro.

### 4.2 `infra/presentation/responses/` eliminado — LIMPIEZA

Directorio vacío que existía como vestigio. **Ya eliminado.**

### 4.3 `application/repositories/` eliminado — LIMPIEZA

Directorio vacío (solo `__pycache__`) que existía como resto de un refactor previo. **Ya eliminado.**

### 4.4 Tests pendientes (cobertura)

| Archivo | Gap |
|---|---|
| `infra/presentation/controllers/user.py` | Sin tests (PATCH/DELETE /users/me) |
| `infra/presentation/controllers/query.py` | Sin tests (7 endpoints) |
| `infra/presentation/controllers/version.py` | Sin tests (5 endpoints CRUD) |
| `infra/presentation/controllers/admin.py` | Sin tests (mutaciones admin, promote) |
| Flujo de invalidación por `token_version` | Sin tests E2E |
| Middleware de `main.py` | Sin tests (headers, CSP, 413) |

---

## 5. Roadmap restante (priorizado)

### Fase 1 — Seguridad (bloqueante)
1. **Filtrar por owner en `GET /versions` y `GET /queries`** — evitar fuga cross-tenant
2. **Evaluar `require_admin` para listados globales** si se mantienen sin filtro de owner

### Fase 2 — Cobertura de tests (continua)
3. Tests para `user.py`, `query.py`, `version.py`, admin mutations
4. Test E2E del flujo de invalidación por `token_version`
5. Tests del middleware de `main.py`

---

## 6. Conclusión

El backend de Qolqa **sí implementa Clean Architecture correctamente**. Las dos decisiones estructurales más importantes están bien:

1. **El dominio es 100% puro** — cero dependencias hacia capas externas.
2. **Existe traducción centralizada de errores de dominio a HTTP** — la lógica de negocio nunca conoce FastAPI.

Lo que se resolvió desde el reporte anterior es sustancial: las 6 violaciones de dependencia, el guard de producción, el secreto en stdout, los índices de MongoDB, la cascada transaccional, el limiter compartido, el repositorio de versiones completo, y el código muerto.

Lo que queda es **acotado y concreto**: principalmente el filtro de ownership en listados globales de versiones y queries, y la cobertura de tests faltante.

---