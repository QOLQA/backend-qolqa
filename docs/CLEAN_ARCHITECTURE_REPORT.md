# Reporte de Arquitectura — Backend Qolqa (Clean Architecture)

**Repositorio:** `backend-qolqa`
**Commit analyzed:** `55a7087` (`chore: remove directory`)
**Fecha:** 2026-10-21
**Stack:** Python 3.10+ (Dockerfile: 3.12) · FastAPI 0.110.3 · Motor 3.6.0 · MongoDB · Pydantic v2 · python-jose · bcrypt · slowapi

---

## 1. Resumen ejecutivo

El backend de **Qolqa** implementa Clean Architecture con **5 capas** y **4 dominios de negocio** (`auth`, `query`, `solution`, `version`). La migración se ejecutó con una estrategia *strangler* bottom-up: cada dominio se migró en un PR independiente, tocando las 4 capas de punta a punta, y el código legacy se eliminó al final.

**Estado de las reglas de dependencia (verificado con `grep` sobre el código fuente):**

| Regla | Estado | Detalle |
|---|---|---|
| `domain/` no importa de otras capas | ✅ **Cumple al 100%** | Cero imports hacia `application/`, `infrastructure/`, `api/`, `config/` |
| `application/` no importa de `api/` | ✅ **Cumple** | Cero imports de `fastapi`, `starlette`, `HTTPException` |
| `application/` no importa de `config/` | ✅ **Cumple** | `settings` se inyecta como parámetro, no se importa |
| `application/` no importa de `infrastructure/` | ❌ **6 violaciones** | 4 archivos del dominio `auth` + 1 de `solution` |
| `infrastructure/` no lanza `HTTPException` | ⚠️ **2 módulos** | `mongo_utils.py` y `db_timeout.py` — ambos **código muerto** |
| Errores de dominio en repositorios | ✅ **Cumple** | Los 4 repositorios lanzan solo `Missing`/`Duplicate` |
| `HTTPException` solo en `api/` | ✅ **Cumple en producción** | Las 2 excepciones están en módulos no importados |

**Métricas del codebase:**

| Métrica | Valor |
|---|---|
| Endpoints REST | **31** (30 versionados + `GET /health`) |
| Casos de uso (application layer) | **21** (auth 4, query 7, solution 5, version 5) |
| Entidades de dominio | 5 aggregates + 5 value objects recursivos |
| Interfaces de repositorio (domain) | 4 (`IUserRepository`, `IQueryRepository`, `ISolutionRepository`, `IVersionRepository`) |
| Implementaciones de repositorio | 4 (`*RepoImpl`) |
| Mappers (dict ↔ entidad) | 4 |
| Clases de error de dominio | 9 |
| Tests | **161** (150 pasan · 4 fallan · 7 skip) |
| Módulos de código muerto | 3 (`documents/`, `db_timeout.py`, `mongo_utils.py`) |
| Commits de la migración | 9 (PRs #50 – #58) |

**Veredicto:** la arquitectura está **estructuralmente bien montada** (el dominio es puro, la capa de aplicación existe y está poblada, los errores de dominio están correctamente desacoplados del HTTP), pero **la disciplina de dependencias se rompió de forma concentrada en el dominio `auth`**, y hay **tres riesgos de seguridad reales** (fuga de secretos en logs, fuga cross-tenant en listados, guard de producción inactivo) más **un bug de autorización** (mutaciones de `version` sin verificación de ownership).

---

## 2. Fundamento teórico: qué es Clean Architecture y cómo se materializa aquí

Clean Architecture (Robert C. Martin) propone separar el software en **capas concéntricas** donde las dependencias apuntan **hacia adentro**: el dominio no conoce nada del exterior, y las capas externas se adaptan a contratos definidos hacia adentro.

En este proyecto las reglas se materializan en tres mecanismos concretos:

### 2.1 La regla de la Dependency Inversion

Las interfaces de repositorio **viven en `domain/`**, no en `infrastructure/`:

```
domain/repositories/user/repo.py     → interface Repository (ABC, Generic)
domain/repositories/query/repo.py    → interface IQueryRepository
domain/repositories/solution/repo.py → interface ISolutionRepository
domain/repositories/version/repo.py  → interface IVersionRepository
```

`infrastructure/repositories/` contiene las implementaciones concretas (`UserRepoImpl`, etc.) que heredan de esas interfaces. La capa de aplicación depende de las **interfaces**, y la infraestructura depende de las **interfaces**: la dependencia se invierte respecto de la estructura de carpetas, que es justamente el punto.

### 2.2 La traducción de errores (el "boundary" entre dominio y HTTP)

El dominio no conoce el protocolo HTTP. Define 9 errores propios en `domain/errors.py`, y un único punto de traducción los mapea a códigos HTTP en `api/handle_errors.py`:

```python
# api/handle_errors.py — tabla de despacho por tipo
Format                       → 400
Missing / NotFoundError      → 404
Forbidden                    → 403
Duplicate                    → 409
InvalidCredentials           → 401  (WWW-Authenticate: Bearer)
InvalidToken                 → 401  (WWW-Authenticate: Bearer)
InvalidGoogleToken           → 401  (WWW-Authenticate: Bearer)
PasswordRequiredForLocalLogin→ 403
GoogleLoginNotConfigured     → 503
cualquier otro               → 500
```

Este es el patrón que permite que `domain/` y `application/` no importen jamás `fastapi`.

### 2.3 La separación de DTOs de contrato vs. DTOs de aplicación

- `application/dtos/<dominio>/<X>Request.py` → **contrato de entrada** (validación de entrada, sanitización).
- `application/dtos/<dominio>/<X>Response.py` → **contrato de salida** (nunca expone `hashed_password`).
- `domain/entities/` → **modelo de negocio** (no es un DTO; no tiene alias de serialización).

Los `Response` usan `Field(serialization_alias="_id")` + `populate_by_name = True` para exponer el `_id` de MongoDB como string en la respuesta, mientras las entidades de dominio usan `id`.

---

## 3. Mapa de capas y dependencias reales

### 3.1 Estructura de directorios

```
backend-qolqa/
├── main.py                          # Composition root: app, middleware, routers, lifespan
├── config/                          # Settings, Mongo client, motor boilerplate
│   ├── settings.py                  # Pydantic Settings (env-driven)
│   ├── mongo.py                     # AsyncIOMotorClient singleton + pool/timeouts
│   └── sql.py                       # Scaffold SQLAlchemy (NO funcional)
│
├── domain/                          # ◀── REGLA DE ORO: no importa nada externo
│   ├── entities/                    # Modelo de negocio
│   │   ├── QueryEntity.py
│   │   ├── SolutionEntity.py
│   │   ├── VersionEntity.py         # + 5 value objects recursivos
│   │   └── auth/{UserEntity, TokenEntity}.py
│   ├── enums/{RoleEnum, AuthProviderEnum}.py
│   ├── errors.py                    # 9 errores de dominio
│   └── repositories/                # Interfaces (contratos)
│       ├── user/repo.py             # + ABC genérico `Repository`
│       ├── query/repo.py
│       ├── solution/repo.py
│       └── version/repo.py
│
├── application/                     # ◀── Orquestación; depende de domain
│   ├── dtos/{auth,query,solution,version}/
│   └── use_cases/{auth,query,solution,version}/   # 21 funciones async
│
├── infrastructure/                  # ◀── Adaptadores técnicos
│   ├── repositories/                # 4 implementaciones Motor
│   ├── mappers/                     # 4 mappers dict ↔ entidad
│   ├── documents/                   # ⚠️ CÓDIGO MUERTO
│   ├── services/google_auth.py
│   ├── jwt.py · token_service.py · password.py
│   ├── audit.py                     # Auditoría a archivo JSON-lines
│   ├── base.py · db_factory.py · db_timeout.py · mongo_utils.py
│
├── api/                             # ◀── HTTP: controllers, dependencies, error mapping
│   ├── controllers/{auth,user,admin,query,version,solution}.py
│   ├── dependencies/auth.py
│   └── handle_errors.py
│
├── tests/                           # 161 tests (8 archivos)
├── openspec/                        # 1 change (google-login) sin archivar
├── scripts/                         # ⚠️ VACÍO (solo __pycache__)
├── schemas/solution.py              # ⚠️ Relic pre-refactor (SQLAlchemy)
└── docs/                            # Este reporte
```

### 3.2 Diagrama de dependencias (verificado por análisis de imports)

```
        ┌──────────────────────────────────────────────┐
        │              api/  (HTTP)                    │
        │  controllers · dependencies · handle_errors  │
        └───────────────┬──────────────────────────────┘
                        │ ▲
                        │ │  ← 6 imports (VIOLACIÓN)
                        ▼ │
        ┌──────────────────────────────────────────────┐
        │          application/  (use cases)           │
        │  21 use cases · 8 archivos de DTO           │
        └───────────────┬──────────────────────────────┘
                        │
                        ▼
        ┌──────────────────────────────────────────────┐
        │            domain/  (núcleo)                 │
        │  entities · enums · errors · repository ABCs │
        └──────────────────▲───────────────────────────┘
                           │  implements
        ┌──────────────────┴───────────────────────────┐
        │        infrastructure/  (adaptadores)        │
        │  repos impl · mappers · jwt · password · …   │
        └──────────────────────────────────────────────┘
```

`domain/` no tiene ninguna flecha saliente. Es el único anillo que cumple la regla al 100%.

---

## 4. Capa `domain/` — El núcleo de negocio

### 4.1 Entidades

Todas las entidades son `BaseModel` de **Pydantic v2** (no dataclasses). Es una decisión discutible — acopla el dominio a un framework de terceros — pero no viola ninguna regla de capa, ya que Pydantic es una librería, no una capa.

| Entidad | Campos | Invariantes |
|---|---|---|
| `QueryEntity` | `id`, `full_query` (1–10000), `collections[]`, `highlighted_words[]`, `solution_id` | `full_query` no vacío + normalizado con `.strip()` |
| `SolutionEntity` | `id`, `name` (1–200), `user_id`, `last_version_saved`, `src_img`, `last_updated_at?`, `versions[]` | Ninguna (ownership verificado en use case) |
| `VersionEntity` | `id`, `submodels[]`, `description`, `solution_id` | Ninguna |
| `UserEntity` | `id`, `username`, `email`, `full_name?`, `is_active`, `created_at`, `profile_picture_url?`, `roles[]`, `token_version`, `google_id?`, `auth_provider` | **`hashed_password` ausente por diseño** |

**`UserEntity` sin `hashed_password`** es una decisión de seguridad deliberada, registrada en `openspec/changes/google-login/design.md` (decisión #7). La consecuencia architectónica es importante y se analiza en §7.1.

### 4.2 Value objects recursivos (`VersionEntity.py`)

El modelo de versiones representa un **esquema de base de datos en forma de grafo**:

```python
class Position:    x: float, y: float
class Column:      id: str, name: str, type: str
class NestedNode:  id, name, cols: List[Column], nested_nodes: Optional[List['NestedNode']], cardinality
class Node:        id, name, type, position, cols, nested_nodes: Optional[List[NestedNode]]
class Edge:        id, source, target, cardinality
```

`NestedNode` es **auto-recursivo** (`Optional[List['NestedNode']]`), lo que permite expresar profundidad arbitraria del modelo relacional. Estos value objects **se reutilizan directamente en la capa de aplicación** (`application/dtos/version/` importa `Submodel` desde `domain/`), evitando duplicar un grafo profundo en los DTOs.

### 4.3 Taxonomía de errores (`domain/errors.py`)

| Error | HTTP | Notes |
|---|---|---|
| `Missing` | 404 | Lanzado por los 4 repositorios (no encontrado **y** id malformado) |
| `NotFoundError` | 404 | Semánticamente duplicado de `Missing`; nunca lanzado |
| `Duplicate` | 409 | username/email/google_id duplicados |
| `Format` | 400 | **Nunca lanzado** — error muerto |
| `Forbidden` | 403 | Ownership violation |
| `InvalidCredentials` | 401 | |
| `InvalidToken` | 401 | Lanzado por `infrastructure/jwt.py` (capa técnica → error de dominio) |
| `PasswordRequiredForLocalLogin` | 403 | Guard de cuenta Google sin password |
| `InvalidGoogleToken` | 401 | |
| `GoogleLoginNotConfigured` | 503 | `GOOGLE_CLIENT_ID` ausente |

### 4.4 Contratos de repositorio

El ABC genérico vive en `domain/repositories/user/repo.py` (ubicación mejorable — debería ser `domain/repositories/base.py`):

```python
class Repository(ABC, Generic[T, TCreate, TUpdate]):
    async def get_by_id(self, id: str | int) -> T
    async def add(self, entity_create: TCreate) -> T
    async def get_all(self) -> List[T]
    async def update(self, id: str | int, entity_update: TUpdate) -> T
    async def delete(self, id: str | int) -> None
```

Interfaces derivadas:

- `IUserRepository` — agrega `get_by_username`, `get_by_email`, `get_by_google_id`, `link_google_account`, `add_google_user`
- `IQueryRepository` — agrega `get_by_solution_id`, `delete_by_solution_id`
- `ISolutionRepository` — agrega `get_all_for_user`
- `IVersionRepository` — **`pass`** ⚠️ no declara ningún método específico

### 4.5 Mapper genérico como abstracción de persistencia

Cada repositorio implementa un `*Mapper` con métodos estáticos que traducen entre el `dict` crudo de MongoDB y la entidad de dominio:

```python
class QueryMapper:
    @staticmethod
    def to_entity_from_dict(raw: dict) -> QueryEntity: ...
    @staticmethod
    def from_create_request(request: QueryCreateRequest) -> dict: ...
    @staticmethod
    def to_response(entity: QueryEntity) -> QueryResponse: ...
```

El mapper es **el único lugar** donde se hace conversión de `ObjectId` ↔ `str` y renombrado de `_id` → `id`. Los repositorios nunca construyen entidades a mano.

---

## 5. Capa `application/` — Orquestación

### 5.1 Convenciones

- Un archivo = un caso de uso, nombre `PascalCase` (`CreateSolution.py`), función `snake_case` async.
- **No hay clases** — son funciones procedurales con dependencias inyectadas por parámetro.
- Los casos de uso son **funciones de una línea** en su mayoría: `return await repository.add(request)`.

### 5.2 Catálogo de los 21 casos de uso

| # | Caso de uso | Repositorio (tipo) | Errores de dominio | Notas |
|---|---|---|---|---|
| 1 | `auth/AuthenticateUser.py` | `UserRepositoryImpl` ⚠️ | `InvalidCredentials`, `PasswordRequiredForLocalLogin` | Importa `infrastructure.password` ⚠️ |
| 2 | `auth/GoogleLogin.py` | `UserRepositoryImpl` ⚠️ | `GoogleLoginNotConfigured`, `InvalidGoogleToken`, `Duplicate` | Importa `infrastructure.services.google_auth` ⚠️ |
| 3 | `auth/GetUserById.py` | `IUserRepository` ✅ | — (repo: `Missing`) | **El único caso de uso auth correctamente tipado** |
| 4 | `auth/RegisterUser.py` | `UserRepositoryImpl` ⚠️ | — (repo: `Duplicate`) | Pass-through; el hashing vive en el repo |
| 5–11 | `query/*.py` (7) | `IQueryRepository` ✅ | — | Delegaciones puras, **sin lógica de negocio** |
| 12 | `solution/CreateSolution.py` | `ISolutionRepository` ✅ | — | Importa `infrastructure.mappers.SolutionMapper` ⚠️ |
| 13 | `solution/GetAllSolutionsForUser.py` | `ISolutionRepository` ✅ | — | Filtra por owner **en la query Mongo** |
| 14 | `solution/GetSolutionById.py` | `ISolutionRepository` ✅ | — | **Muta** la entidad devuelta por el repo |
| 15 | `solution/UpdateSolution.py` | `ISolutionRepository` ✅ | `Forbidden` | Verifica ownership ✅ |
| 16 | `solution/DeleteSolution.py` | `ISolutionRepository` + `IVersionRepository` + query repo | `Forbidden` | **Cascada no transaccional** |
| 17–21 | `version/*.py` (5) | `IVersionRepository` ✅ | — | **Sin verificación de ownership** ⚠️ |

### 5.3 Ejemplo de flujo de orquestación real: `GoogleLogin`

Es el caso de uso más complejo del proyecto y el único con manejo de concurrencia:

```
1. Guard de configuración    → if client_id is None: raise GoogleLoginNotConfigured (503)
2. Verificación del token    → verify_google_token(credential, client_id)  [infra, off-thread]
                                valida sub + email + email_verified
3. Resolver por google_id    → get_by_google_id(sub) → si existe, devolver
4. Linking por email (híbrido) → solo si email_verified:
                                  get_by_email(email) → link_google_account(user.id, sub)
                                  on Duplicate → re-fetch por google_id (recuperación de carrera)
5. Crear usuario nuevo       → loop attempt 0..100:
                                  username = base | base1 | … | base100
                                  add_google_user(...)  [sin hashing]
                                  on Duplicate → (a) re-fetch google_id
                                               (b) si email_verified → intentar link
                                               (c) si attempt == 100 → re-raise
                                               (d) siguiente sufijo
```

Tres rutas de recuperación de carrera distintas, todas cubiertas por tests.

---

## 6. Capa `infrastructure/` — Adaptadores técnicos

### 6.1 Repositorios (4 implementaciones)

Patrón común a los 4:

1. Constructor recibe la **base de datos**, no la colección: `self.collection = database['queries']`.
2. Validación de ObjectId → `Missing` (nunca `HTTPException`).
3. Traducción de errores: solo `Missing` y `Duplicate`.
4. Updates parciales con `model_dump(exclude_unset=True)` — nunca sobreescriben con `None`.
5. Read-after-write en `add()`/`update()` para devolver el estado persistido canónico.

| Repositorio | Colecciones | Métodos | Detalles |
|---|---|---|---|
| `UserRepoImpl` | `users` | 10 | `get_hashed_password` usa **projection** (`{'hashed_password': 1}`); `update` usa `mode='json'` para serializar enums; detecta duplicados por username/email/google_id |
| `QueryRepoImpl` | `queries` + `solutions` | 7 | **Verifica que la solución padre exista** antes de insertar; `solution_id` se almacena como `ObjectId` |
| `VersionRepoImpl` | `versions` + `solutions` | 7 | **Verifica solución padre**; `solution_id` se almacena como `str`; re-serializa `submodels` en updates |
| `SolutionRepoImpl` | `solutions` (+`versions` sin usar) | 6 | `add(entity_create: dict)` — el `TCreate` genérico está ligado a `dict`; `update` siempre sella `last_updated_at` |

**Integridad referencial:** la verificación de existencia del padre ocurre en la capa de infraestructura (MongoDB no tiene foreign keys). `Query` y `Version` la implementan; `Solution` no aplica (es la raíz).

### 6.2 Servicios técnicos

| Módulo | Responsabilidad | Detalle |
|---|---|---|
| `jwt.py` | Creación/validación de tokens | HS256, `python-jose`, payload con `sub`, `user_id`, `email`, `roles`, `token_version`, `exp`, `iat`, `type`. Lanza `InvalidToken` (error de **dominio**) — respeta la regla |
| `token_service.py` | Ensamblado del token | `create_user_token(user)` → `TokenResponse`. `roles` y `token_version` incluidos (requisito AGENTS.md) |
| `password.py` | Hashing | bcrypt, **cost factor 12**. `verify_password` / `get_password_hash` |
| `services/google_auth.py` | Verificación OAuth | `asyncio.to_thread(...)` para no bloquear el event loop; valida `sub`, `email`, `email_verified`; lanza `InvalidGoogleToken` |
| `audit.py` | Auditoría | `RotatingFileHandler` (10 MB × 5) + `JSONFormatter` (JSON-lines). 6 funciones: `log_audit`, `log_auth_attempt`, `log_registration`, `log_resource_operation`, `log_access_denied`, `log_rate_limit_exceeded` |
| `base.py` | Bases Pydantic | `MongoBaseModel` (`id: PyObjectId` con alias `_id`), `SQLBaseModel` (sin uso), anotación `PyObjectId` que acepta `str` y serializa a `str` |
| `db_factory.py` | Resolución de backend | Selección **en tiempo de llamada**, no de import: mongo → `config.mongo`, sql → `config.sql` |

### 6.3 `config/`

`settings.py` — `Settings(BaseSettings)` con `env_file='.env'`: `database_url`, `type_db`, `secret_key` (min 32 chars), `algorithm`, `access_token_expire_minutes` (300), `environment`, `allowed_origins`, `db_operation_timeout` (10s), `google_client_id`, `max_request_body_size` (5 MB).

`mongo.py` — `AsyncIOMotorClient` singleton a nivel de módulo (Motor es lazy: no conecta hasta la primera operación). Timeouts: `socketTimeoutMS` (derivado de `db_operation_timeout`), `connectTimeoutMS` 5s, `serverSelectionTimeoutMS` 5s. Pool: `maxPoolSize=50`, `minPoolSize=10`.

---

## 7. Capa `api/` — HTTP

### 7.1 Bootstrap (`main.py`)

**Stack de middleware** (orden de ejecución: externo → interno):

| # | Middleware | Efecto |
|---|---|---|
| 1 | `CORSMiddleware` | Orígenes desde settings (sin wildcard), `allow_credentials=True`, métodos `GET/POST/PATCH/DELETE/OPTIONS`, `max_age=3600` |
| 2 | `add_security_headers` | HSTS (solo en producción), `X-Content-Type-Options`, `X-Frame-Options: DENY`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`, **CSP** (relajado para `/docs`) |
| 3 | `log_requests` | Log method/path/status + header `X-Process-Time` |
| 4 | `RequestSizeLimitMiddleware` | 413 si `Content-Length` > 5 MB |

**Rate limiting:** `slowapi` con `Limiter(key_func=get_remote_address)`. Handler custom: decodifica el bearer token best-effort para atribuir el offenders, escribe en el audit log, y responde `429` con `Retry-After`.

**Lifespan:** dos ramas según `settings.type_db`. La rama Mongo **no crea índices** ni cierra el cliente al apagar.

### 7.2 Endpoints (31)

#### `/auth` — `api/controllers/auth.py`
| Método | Ruta | Auth | Rate limit | Use case |
|---|---|---|---|---|
| POST | `/auth/register` | — | `3/hour` | `register_user` |
| POST | `/auth/login` | — | `5/minute` | `authenticate_user` |
| GET | `/auth/me` | `get_current_user` | — | mapper directo |
| POST | `/auth/google` | — | `5/minute` | `google_login` |

#### `/users` — `api/controllers/user.py` (sin use cases, acceso directo al repo)
| Método | Ruta | Auth | Body |
|---|---|---|---|
| PATCH | `/users/me` | `get_current_user` | `UserUpdateRequest` (sin `roles` ni `token_version`) |
| DELETE | `/users/me` | `get_current_user` | — |

#### `/admin` — `api/controllers/admin.py` (todos `require_admin`, **sin rate limiting**)
| Método | Ruta | Notas |
|---|---|---|
| GET | `/admin/users` | |
| GET | `/admin/users/{user_id}` | |
| PATCH | `/admin/users/{user_id}` | `AdminUserUpdateRequest` + `$inc token_version` si cambian roles |
| DELETE | `/admin/users/{user_id}` | |
| POST | `/admin/users/{user_id}/promote` | **Idempotente** — si ya es admin, devuelve estado sin efectos |

#### `/queries` — `api/controllers/query.py` (7 endpoints)
`GET /queries` · `GET /queries/solution/{solution_id}` · `GET /queries/{query_id}` · `POST /queries` · `PATCH /queries/{query_id}` · `DELETE /queries/{query_id}` · `DELETE /queries/solution/{solution_id}`

#### `/versions` — `api/controllers/version.py` (5 endpoints)
`GET /versions` · `GET /versions/{version_id}` · `POST /versions` · `PATCH /versions/{version_id}` · `DELETE /versions/{version_id}`

#### `/solutions` — `api/controllers/solution.py` (7 endpoints)
`GET /solutions` · `POST /solutions` · `GET /solutions/{id}` · `PATCH /solutions/{id}` · `POST /solutions/{solution_id}/versions` · `PATCH /solutions/{solution_id}/versions/{version_id}` · `DELETE /solutions/{id}` (cascada)

#### Salud
`GET /health` — ping real a Mongo (`motor_client.admin.command('ping')`), `200`/`503`. Sin auth, sin rate limit.

### 7.3 Dependencias de autenticación (`api/dependencies/auth.py`)

```python
get_token_data(token)          # decodifica JWT; InvalidToken → 401
get_current_user(token_data, repository)
    ├── valida sub + user_id presentes            → 401
    ├── get_user_by_id(...)                        # 1 lectura a DB por request
    ├── if not entity.is_active                   → 403
    └── token_version != entity.token_version      → 401  (token invalidado)
require_admin(token_data, current_user)
    └── lee roles del PAYLOAD del JWT, sin query extra → 403
```

Cumple la regla de AGENTS.md: `require_admin` **no** hace query adicional (lee los roles del JWT), y `token_version` **se valida contra la DB en cada request** (costo: 1 lectura por request autenticado).

### 7.4 Uso de casos con lógica de negocio — y dónde NO debería estar

El `api/` layer contiene **9 sitios** con lógica de negocio que deberían estar en `application/`:

| Ubicación | Lógica |
|---|---|
| `solution.py:137, 214, 257` | Verificación de ownership **repetida 3 veces con 3 mensajes distintos** |
| `solution.py:76-119` | Orquestación de 3 pasos al crear una solución (crear → crear versión → actualizar `last_version_saved`) |
| `solution.py:213-225` / `255-265` | Creación y actualización de versiones anidadas (use cases disfrazados) |
| `admin.py:59-66` / `114-119` | Invalidación de token (`$inc token_version` + re-fetch) duplicada en 2 endpoints |
| `admin.py:100-105` | Mutación del set de roles + check de idempotencia |
| `solution.py:102-105` | `logger.info(pprint.pformat(...))` del payload completo — debug en producción |

La regla de ownership está implementada en **5 lugares distintos con 5 mensajes diferentes** (3 en controllers, 2 en use cases), y `GetSolutionById` **no** la tiene — el guard vive en el controller en su lugar.

---

## 8. Configuración de seguridad implementada

| Control | Implementación | Estado |
|---|---|---|
| Hashing de passwords | bcrypt, cost 12, salt por usuario | ✅ |
| JWT firmado | HS256, `secret_key` de `settings`, `exp` 300 min | ✅ |
| `roles` en el payload | `token_service.create_user_token` | ✅ |
| `token_version` en el payload + validación por request | `$inc` atómico en admin controller | ✅ |
| Revocación de tokens | `token_version` mismatch → 401 | ✅ |
| Escalada de privilegios | `UserUpdateRequest` **no tiene** `roles` ni `token_version` — imposible por construcción | ✅ |
| Guard de admin | Lee roles del JWT, sin query extra | ✅ |
| Rate limiting | slowapi en auth y CRUD; **ausente en `/admin`** | ⚠️ |
| Headers de seguridad | HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy | ✅ |
| Límite de tamaño de request | 5 MB vía `Content-Length` | ⚠️ (chunked lo evade) |
| Auditoría | JSON-lines rotado en `logs/audit.log` | ⚠️ (solo archivo, no persistida en DB) |
| OAuth Google | Verificación de `sub`/`email`/`email_verified` + 3 recuperación de carrera | ✅ |
| CORS | Orígenes específicos, sin wildcard | ✅ |
| Health check | Ping real a la DB | ✅ |
| Secret key en producción | Validator que rechaza defaults inseguros | 🔴 **No se ejecuta** (§9.1) |

---

## 9. Findings — Deuda técnica, riesgos y bugs

Ordenados por severidad. Todos verificados con inspección del código fuente; los tests se ejecutaron con Python 3.11 en un venv limpio.

### 🔴 Críticos

#### 9.1 El guard de `secret_key` en producción nunca se ejecuta
`config/settings.py`: `secret_key` está declarado en la **línea 17** y `environment` en la **línea 25**. El `@field_validator('secret_key')` lee `info.data.get('environment', 'development')`, pero `info.data` solo contiene los campos **ya validados**. Como `environment` se declara después, nunca está presente → el validator siempre evalúa `'development'` → **la protección nunca dispara en producción**.

```python
# config/settings.py:54-75
@field_validator('secret_key')
def validate_secret_key_in_production(cls, v: str, info) -> str:
    environment = info.data.get('environment', 'development')   # ← siempre 'development'
    if environment == "production" and v.lower() in [...]:
        raise ValueError("🔒 SECURITY ERROR: ...")
```

**Fix:** mover `environment` por encima de `secret_key`, o usar `@model_validator(mode='after')`.

#### 9.2 `print(settings)` filtra el `secret_key` a stdout en cada arranque
`main.py:140` y `main.py:147` imprimen el objeto `Settings` completo. `secret_key` es un `str` plano (no `pydantic.SecretStr`), así que el `__repr__` lo renderiza en claro al stdout del contenedor en cada boot. **Fix:** eliminar los `print(settings)` o usar `SecretStr`.

#### 9.3 Fuga de datos cross-tenant en `GET /versions` y `GET /queries`
`VersionRepoImpl.get_all()` y `QueryRepoImpl.get_all()` **no filtran por owner**. Cualquier usuario autenticado puede listar **todas las versiones** (que contienen el `submodels` completo: el diseño del esquema de base de datos de cada solución) y **todas las queries**. `GET /queries` además documenta *"admin endpoint"* en su docstring **pero no tiene `require_admin`**.

Contraste: `GET /solutions` **sí** filtra por owner vía `get_all_for_user`.

#### 9.4 Mutaciones de `version` sin verificación de ownership
`update_version` y `delete_version` **no** verifican que la versión pertenezca al usuario autenticado, mientras que `update_solution` y `delete_solution` **sí** lo hacen. Un usuario que conozca un `version_id` ajeno puede modificarlo o borrarlo. `VersionEntity` tiene `solution_id`, así que la comprobación es implementable — simplemente no está.

### 🟠 Altos

#### 9.5 Las 6 violaciones `application → infrastructure`
```
application/use_cases/auth/GoogleLogin.py:16    from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl
application/use_cases/auth/GoogleLogin.py:17    from infrastructure.services.google_auth import verify_google_token
application/use_cases/auth/AuthenticateUser.py:3  from infrastructure.password import verify_password
application/use_cases/auth/AuthenticateUser.py:7  from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl
application/use_cases/auth/RegisterUser.py:3      from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl
application/use_cases/solution/CreateSolution.py:4 from infrastructure.mappers.SolutionMapper import SolutionMapper
```

**Causa raíz (no es descuido, es consecuencia forzada del diseño):**
1. `UserEntity` excluye `hashed_password` por seguridad (decisión #7 del design).
2. Por lo tanto `AuthenticateUser` no puede obtener el hash de la entidad.
3. El hash solo es accesible vía `UserRepositoryImpl.get_hashed_password()` — un método **fuera** de `IUserRepository` (correctamente: un hash no pertenece al contrato de dominio).
4. Entonces el caso de uso debe importar la **clase concreta** de infraestructura.

**El fix arquitectónico correcto es un puerto:** agregar a `domain/` un contrato `IPasswordHasher` / `verify_credentials(username, password) -> bool`, con la implementación bcrypt en `infrastructure/`. Esto elimina 2 de las 6 violaciones y habilita testear `AuthenticateUser` sin bcrypt real.

El propio `openspec/changes/google-login/explore.md:18` ya identificaba la violación y la marcaba como *"pre-existing tech debt"* — pero `GoogleLogin.py` (creado por ese mismo change) **introdujo 2 violaciones nuevas**, justificándolas por precedencia circular.

#### 9.6 `IVersionRepository` está vacío
```python
class IVersionRepository(Repository[T, TCreate, TUpdate]):
    pass
```
`get_by_solution_id` y `delete_by_solution_id` existen en `VersionRepoImpl` pero **no están declarados en la interfaz**. `DeleteSolution` llama `version_repository.delete_by_solution_id(...)` mediante duck typing sobre un método no declarado. El contrato de dominio está objetivamente incompleto y asimétrico con `IQueryRepository`.

#### 9.7 Nunca se crea ningún índice en MongoDB
Cero llamadas a `create_index` en todo el código de producción (verificado). Consecuencias:
- Todos los lookups son **collection scans**.
- Los handlers de `DuplicateKeyError` en `UserRepoImpl` son **código muerto** (no hay índices únicos que los disparen).
- La detección de duplicados es check-then-insert → **condición de carrera real** bajo concurrencia.
- La protección de carrera que `GoogleLogin` implementa (3 rutas de recuperación) depende de un índice único sparse en `google_id` que **nunca se creó**: el script `scripts/migrate_add_google_fields.py` que lo hacía fue borrado en el commit `55a7087`.

**Índices mínimos:** `users.username` (unique), `users.email` (unique), `users.google_id` (unique, sparse), `queries.solution_id`, `versions.solution_id`, `solutions.user_id`.

#### 9.8 La suite de tests tiene 4 fallos
```
FAILED tests/test_google_login.py::TestMigrationScriptBehavioral::test_dry_run_does_not_call_update_many
FAILED tests/test_google_login.py::TestMigrationScriptBehavioral::test_real_mode_calls_update_many_and_create_index
FAILED tests/test_google_login.py::TestMigrationScriptBehavioral::test_dry_run_prints_matched_docs_and_index_spec
FAILED tests/test_rate_limiting.py::TestRateLimiting::test_login_rate_limit
```
- Los 3 primeros: `ModuleNotFoundError` — `scripts/` contiene **solo** `__pycache__/migrate_add_google_fields.cpython-311.pyc`. El `.py` se borró en `55a7087` pero los tests siguen importándolo. Además falta `scripts/__init__.py`.
- El cuarto: requiere un MongoDB vivo en `localhost:27017` (el fixture `client` no overridea la DB) → `ServerSelectionTimeoutError`.

### 🟡 Medios

| # | Finding | Evidencia |
|---|---|---|
| 9.9 | **Cascada de borrado no transaccional** | `DeleteSolution` hace 3 llamadas separadas (queries → versions → solution). Un fallo en el paso 2 deja queries borradas y versions presentes. MongoDB standalone no soporta transacciones multi-documento |
| 9.10 | **Sin paginación ni ordenamiento** | Todos los `get_all()` hacen `find().to_list(length=None)` — escaneo completo con memoria no acotada. Vector de OOM/DoS |
| 9.11 | **5 instancias de `Limiter`** | `main.py:50`, `auth.py:25`, `query.py:23`, `version.py:21`, `solution.py:33`. Cada una crea su propio `MemoryStorage` → contadores independientes. Con `--workers 2` (Dockerfile) los límites efectivos son ~2×. `app.state.limiter` es una instancia decorativa |
| 9.12 | **Sin rate limiting en `/admin`** | `DELETE /admin/users/{id}` y `POST /admin/users/{id}/promote` sin throttling |
| 9.13 | **`infrastructure/documents/` es código muerto** | Los 4 repositorios trabajan con dicts crudos; `QueryMapper.to_entity(doc: QueryDocument)` no tiene llamadores. `SolutionDocument.versions` (embedded) contradice la realidad (colección separada) y `EmbeddedVersion` hereda un `_id` que los embebidos no tienen |
| 9.14 | **`db_timeout.py` y `mongo_utils.py` son código muerto** | `mongo_utils` solo lo referencia `tests/test_security.py`; `db_timeout` solo se referencia a sí mismo. Ambos lanzan `HTTPException` desde `infrastructure/` — violación de capa latente |
| 9.15 | **`solution_id` con tipos inconsistentes** | `queries.solution_id` = `ObjectId`, `versions.solution_id` = `str`. `QueryRepoImpl.delete_by_solution_id` valida el formato; `VersionRepoImpl.delete_by_solution_id` no |
| 9.16 | **Creación de solution en 3 pasos sin transacción** | `solution.py:86-100` — si falla el paso 2 o 3 queda una solution con `last_version_saved="unknown"` |
| 9.17 | **Doble lectura de Mongo por GET de solution** | `solution.py:134` llama `get_by_id`, y `GetSolutionById.py:18` lo llama **otra vez** |
| 9.18 | **`parse_cors_origins` no maneja arrays JSON** | Las dos ramas del validator son idénticas → `'["http://a","http://b"]'` se parte por comas en `['["http://a"', '"http://b"]']` |
| 9.19 | **`datetime.utcnow()` en todo el codebase** | Naive UTC, deprecado en Python 3.12 (el Dockerfile usa 3.12). Mixeado con `datetime.now(timezone.utc)` en el health check |
| 9.20 | **Límite de 72 bytes de bcrypt no validado** | `UserCreateRequest.password` permite `max_length=100` **caracteres**; bcrypt trunca a 72 **bytes**. Una contraseña larga no-ASCII colisiona silenciosamente con su prefijo |
| 9.21 | **El cliente de Mongo nunca se cierra** | No hay `await motor_client.close()` en el lifespan ni en ningún shutdown hook |
| 9.22 | **`VersionPartialUpdateRequest` permite cambiar `solution_id`** | El repo no re-verifica que la nueva solución padre exista → versiones huérfanas. `QueryPartialUpdateRequest` sí excluye `solution_id` a propósito |
| 9.23 | **Auditoría solo en archivo** | No hay colección de auditoría en Mongo ni campos `created_by`/`updated_by`. La rotación (5×10 MB) descarta historia silenciosamente. Además se emite desde los controllers, no desde los repositorios |
| 9.24 | **Docstring contradice el código** | `UpdateSolution.py` documenta `Missing` (404) pero lanza `Forbidden` (403). El código es correcto; el docstring miente |

### 🟢 Bajos

| # | Finding |
|---|---|
| 9.25 | `domain/entities/auth/TokenEntity.py` — cero importadores (duplicado por `TokenResponse`) |
| 9.26 | `domain/errors.py::Format` — declarado y mapeado a 400, nunca lanzado |
| 9.27 | `default_version_descriptions` en `VersionRequest.py:6` — declarado, nunca referenciado |
| 9.28 | `from typing import Optional` sin uso en `AuthenticateUser.py` |
| 9.29 | `UserLoginRequest` DTO declarado, nunca usado (el login usa `OAuth2PasswordRequestForm`) |
| 9.30 | El ABC genérico `Repository` vive en `domain/repositories/user/repo.py` y lo importan los otros 3 paquetes |
| 9.31 | Docstrings en español en `domain/repositories/query/repo.py` y `solution/repo.py` (herencia pre-refactor) |
| 9.32 | `GetSolutionById` muta la entidad devuelta por el repo (`entity.versions = versions`) |
| 9.33 | Implicit Optionals: `versions: List[VersionEntity] = None`, `version_repository: IVersionRepository = None`, `query_repository=None` (sin tipo) |
| 9.34 | `UserResponse.id` sin alias `_id`, inconsistente con Query/Solution/Version |
| 9.35 | `asyncio==3.4.3` en `requirements.txt` — backport de PyPI que **shadowea el stdlib** en Python 3.12 |
| 9.36 | `pytest-cov` ausente aunque el README documenta `pytest --cov` |
| 9.37 | `schemas/solution.py` — relic pre-refactor, fuera del mapa de capas de AGENTS.md; el path SQL no tiene tabla `Version` y ningún repo SQL |
| 9.38 | `tests/README.md` desactualizado (afirma que JWT no está implementado y que los tests están en español) |
| 9.39 | La suite es plana (`tests/test_*.py`), no espeja el árbol de fuentes como exige AGENTS.md |
| 9.40 | `Retry-After: 60` hardcodeado, no coincide con la ventana real del límite (`3/hour`) |

---

## 10. Estrategia de la migración (reconstruida del historial)

El refactor **nunca se especificó en OpenSpec** — se ejecutó como commits convencionales. El patrón es un **strangler bottom-up**:

| Commit | PR | Alcance | Δ líneas |
|---|---|---|---|
| `7bc8b97` | #50 | **Fundación**: esqueleto de `domain/` (errores, enums, 4 ABCs), helpers cross-cutting de `infrastructure/` | +428 |
| `25b7cce` | #51 | **Dominio query** — controller + 7 use cases + entity + mapper + repo | +569 |
| `6669a28` | #52 | **Dominio version** — 5 use cases + `VersionEntity` con los value objects del grafo | +514 |
| `1eaf4fc` | #53 | **Dominio solution** — 5 use cases + `domain/errors.py` + `api/handle_errors.py` + mapper | +790 |
| `920af59` | #54 | **Dominio auth** — 4 use cases + `UserEntity`/`TokenEntity` | +707 |
| `3e9a718` | #55 | **Purga del legacy** — borra `models/`, `interfaces/`, `schemas/`, `utils/` y los routers planos | −2255 |
| `33316ef` | #57 | Roles, perfil, token versioning; `RoleEnum`; `api/dependencies/auth.py`; `admin.py` | +772 |
| `c6ec7ce` | #58 | **Google login** — el único change de OpenSpec | +1866 |
| `55a7087` | — | Borra `scripts/migrate_add_google_fields.py` (el script del PR #58, un commit después) | −107 |

**Lecciones del proceso:**

1. **Fundación primero** — el ABC genérico, la taxonomía de errores y los helpers de infraestructura se extrajeron antes de migrar cualquier dominio.
2. **Una rebanada vertical por dominio** — cada PR tocaba las 4 capas de punta a punta y era mergeable por sí solo.
3. **Legacy al final** — el árbol viejo (`models/` + `routers/` + `services/`) sobrevivió intacto durante los PRs #51–#54 y se borró de una vez en #55 (−2255 líneas).
4. **El dominio `auth` fue migrado al final y se le permitió conservar las violaciones** — porque `AuthenticateUser` necesitaba `verify_password` + `get_hashed_password` y no existía un puerto limpio del que depender.

### 10.1 Estado de OpenSpec

```
openspec/
├── config.yaml              # convenciones: strict_tdd: true, async_mode: true
├── specs/                   # VACÍO — nunca se escribieron specs base
└── changes/
    ├── archive/             # VACÍO — google-login nunca se archivó
    └── google-login/        # proposal · design · spec · tasks · explore
```

`google-login` es un **modelo del workflow correcto** (`explore` → `proposal` → `spec` con Given/When/Then → `design` con tabla de decisiones → `tasks` con 6 work units y checkboxes RED/GREEN TDD). Pero:

- `specs/` vacío → el `spec.md` es un *delta spec* (ADDED/MODIFIED) **sin baseline contra el cual deltaear**.
- `changes/archive/` vacío → el change está 100% implementado (`tasks` todos `[x]`) pero nunca se archivó.
- El NFR del propio spec dice *"No new Clean Architecture violations"*, y la implementación **introdujo 2 nuevas** en `GoogleLogin.py`.

---

## 11. Cobertura de tests

**Resultado real** (Python 3.11.15, venv con `requirements.txt`):

```
4 failed, 150 passed, 7 skipped, 5 warnings in 12.33s
```

| Archivo | Tests | Enfoque |
|---|---|---|
| `test_google_login.py` | 59 | Dominio, mapper, repo, use case, DTOs, endpoint — el file más completo |
| `test_version_validation.py` | 25 | Validación de DTOs de version |
| `test_auth.py` | 22 | JWT, bcrypt, login, registro, roles |
| `test_endpoints.py` | 18 | Integración CRUD de solutions |
| `test_security.py` | 17 | `mongo_utils` — ⚠️ testea código muerto |
| `test_solution_validation.py` | 11 | Validación de DTOs de solution |
| `test_rate_limiting.py` | 9 | Límites (1 requiere Mongo vivo) |

**Estrategia de mocking (3 niveles):**
1. **Endpoint-level** — `patch('api.controllers.solution.get_all_solutions_for_user')`: parchea el *sitio de import*. Funciona solo porque los controllers usan `from X import Y`; si cambiaran a `import X`, los patches fallarían en silencio.
2. **Repository-level** — `patch('api.controllers.solution.SolutionRepositoryImpl.get_by_id')`.
3. **Motor-level** — mock directo de la colección (`mock_collection.find_one`, `update_one`, `insert_one`) con assertions sobre `assert_awaited_once_with(...)`.

**Gaps de cobertura:**
- **Ningún test** para `api/controllers/user.py` (`PATCH /users/me`, `DELETE /users/me`)
- **Ningún test** para `api/controllers/query.py` (los 7 endpoints de query)
- **Ningún test** para `api/controllers/version.py` (los 5 endpoints CRUD de version)
- **Ningún test** para `PATCH/DELETE /admin/users/{id}` ni `POST /admin/users/{id}/promote`
- **Ningún test** end-to-end del flujo de invalidación por `token_version` (el corazón de la feature de roles)
- **Ningún test** del middleware de `main.py` (headers, CSP, `X-Process-Time`, límite 413)
- **Ningún test** del camino genérico 500 de `handle_common_errors`

---

## 12. Roadmap de remediación priorizado

### Fase 1 — Seguridad (bloqueante, ~1 día)
1. Arreglar el orden de campos en `Settings` (o `model_validator(mode='after')`) → §9.1
2. Eliminar `print(settings)` de ambos lifespans; usar `SecretStr` → §9.2
3. Filtrar por owner en `GET /versions` y `GET /queries`; evaluar `require_admin` para el listado global → §9.3
4. Agregar verificación de ownership a `update_version` / `delete_version` → §9.4
5. Restaurar o eliminar `scripts/migrate_add_google_fields.py` (+ `scripts/__init__.py`) → §9.8

### Fase 2 — Corrección de contratos (1 semana)
6. Declarar `get_by_solution_id` y `delete_by_solution_id` en `IVersionRepository` → §9.6
7. Crear los índices MongoDB en el lifespan de Mongo → §9.7
8. Unificar `solution_id` (ObjectId vs str) con migración de datos → §9.15
9. Implementar el puerto `IPasswordHasher` en `domain/` y migrar `AuthenticateUser` / `RegisterUser` → §9.5 (elimina 2 de 6 violaciones)
10. Corregir el docstring de `UpdateSolution`; limpiar `Optional` implícitos → §9.24, §9.33

### Fase 3 — API y operación (1 semana)
11. Mover la lógica de los controllers a use cases (ownership, orquestación de 3 pasos, invalidación de token) → §7.4
12. Unificar las 5 instancias de `Limiter` → §9.11
13. Agregar rate limiting a `/admin` → §9.12
14. Agregar paginación y ordenamiento a los listados → §9.10
15. Cerrar el cliente de Mongo en el lifespan → §9.21
16. Reemplazar `datetime.utcnow()` por `datetime.now(timezone.utc)` → §9.19

### Fase 4 — Saneamiento (1 semana)
17. Eliminar `documents/`, `db_timeout.py`, `mongo_utils.py` (o conectarlos de verdad) → §9.13, §9.14
18. Eliminar código muerto: `TokenEntity`, `Format`, `default_version_descriptions`, `UserLoginRequest` → §9.25–9.29
19. Mover el ABC `Repository` a `domain/repositories/base.py` → §9.30
20. Decidir el destino del path SQL: implementarlo o borrarlo (`config/sql.py`, `schemas/`, `TypeDB.sql`) → §9.37
21. Quitar `asyncio==3.4.3`; agregar `pytest-cov`; actualizar README y `tests/README.md` → §9.35–9.38
22. Archivar el change `google-login` en OpenSpec; escribir los specs base → §10.1

### Fase 5 — Cobertura (continua)
23. Tests para `user.py`, `query.py`, `version.py`, admin mutations, flujo de `token_version`, middleware → §11

---

## 13. Conclusión

El backend de Qolqa **sí implementa Clean Architecture**, y lo hace bien en sus dos decisiones estructurales más importantes: el **dominio es 100% puro** (verificado: cero dependencias hacia afuera) y existe una **traducción centralizada de errores de dominio a HTTP** que permite que la lógica de negocio nunca conozca FastAPI.

La capa de aplicación está **genuinamente poblada** con 21 casos de uso, y los repositorios respetan el contrato de dominio (traducen a `Missing`/`Duplicate`, nunca a `HTTPException`). La separación DTO/entidad/mapper es consistente y hay decisiones de seguridad bien tomadas: `hashed_password` fuera de la entidad, `UserUpdateRequest` sin `roles` (escalada de privilegios imposible por construcción), `token_version` con invalidación atómica, y un guard de Google login con tres rutas de recuperación de carrera.

**Lo que le falta es disciplina en los bordes.** Las 6 violaciones `application → infrastructure` están todas concentradas en el dominio `auth`, y su causa raíz es una decisión de seguridad correcta (`hashed_password` fuera de la entidad) que no fue compensada con el puerto correspondiente. Hay además **cuatro riesgos activos** — el guard de producción que no dispara, el secreto en stdout, dos listados sin filtro de owner, y mutaciones de version sin ownership — que son correcciones concretas y acotadas.

Para un trabajo académico, el proyecto tiene material de sobra: la **estrategia de migración strangler** es un caso de estudio interesante (extracción por dominio, legacy borrado al final, y la tensión entre deuda preexistente y deuda nueva que quedó documentada en el propio OpenSpec). Y hay una lección precisa que conviene reportar: **Clean Architecture no falla por ignorarla, falla cuando una decisión de seguridad de una capa no se compensa con un contrato en la capa correcta**. El puerto de verificación de password no se diseñó, y 4 meses después el dominio auth arrastra la deuda.
