# Reporte de Persistencia — MongoDB (Backend Qolqa)

**Repositorio:** `backend-qolqa`
**Base de datos:** `qolqa` (Motor / MongoDB)
**Driver:** `motor` (async) + `pydantic` v2 para documentos
**Fecha:** 2026-10-26

---

## 1. Resumen ejecutivo

El backend de Qolqa persiste sus datos en **MongoDB** usando el driver asíncrono **Motor** (`AsyncIOMotorClient`). La base de datos se llama `qolqa` y contiene cuatro colecciones principales:

| Colección | Propósito | Entidad de dominio | Documento MongoDB |
|-----------|-----------|-------------------|-------------------|
| `users` | Usuarios del sistema | `UserEntity` | `UserDocument` |
| `solutions` | Canvas / Proyectos (modelos de datos) | `SolutionEntity` | `SolutionDocument` |
| `versions` | Versiones de esquemas JSON (submodels) | `VersionEntity` | `VersionDocument` |
| `queries` | Consultas guardadas asociadas a soluciones | `QueryEntity` | `QueryDocument` |

**Relación entre colecciones:**
- `users` ←1:N→ `solutions` (un usuario tiene muchas soluciones, vía `user_id`)
- `solutions` ←1:N→ `versions` (una solución tiene muchas versiones, vía `solution_id`)
- `solutions` ←1:N→ `queries` (una solución tiene muchas queries, vía `solution_id`)

**Nota importante:** No existe ningún servicio de almacenamiento (Storage) dedicado para archivos binarios o capturas visuales. El campo `src_img` es simplemente una **URL string** que almacena la dirección de una imagen ya subida externamente. Véase §8 para detalles.

---

## 2. Configuración de conexión

Archivo: `config/mongo.py`

```python
motor_client = AsyncIOMotorClient(
    settings.database_url,
    socketTimeoutMS=settings.db_operation_timeout * 1000,
    connectTimeoutMS=5000,
    serverSelectionTimeoutMS=5000,
    maxPoolSize=50,
    minPoolSize=10,
)

database = motor_client['qolqa']
```

- **Cliente:** `AsyncIOMotorClient` (singleton a nivel de módulo, conexión perezosa — no conecta hasta la primera operación)
- **Base de datos:** `qolqa`
- **Pool:** 50 conexiones máximas, 10 mínimas
- **Timeouts:** socket y server-selection configurables vía `settings.db_operation_timeout` (default 10s)

---

## 3. Colección `users` — Usuarios

**Archivos:**
- Dominio: `domain/entities/auth/UserEntity.py`
- Documento: `infra/persistence/documents/UserDocument.py`
- Repositorio: `infra/persistence/repositories/UserRepoImpl.py`
- Mapper: `infra/persistence/mappers/UserMapper.py`

### 3.1 Esquema del documento MongoDB (`users`)

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `_id` | `ObjectId` | Sí | Clave primaria de MongoDB (alias `id`) |
| `username` | `str` | Sí | Nombre de usuario (minúsculas, único) |
| `email` | `str` | Sí | Correo electrónico (minúsculas, único) |
| `full_name` | `str` | No | Nombre completo |
| `is_active` | `bool` | Sí | Estado de activación de la cuenta |
| `hashed_password` | `str` | No | Hash bcrypt de la contraseña (solo auth local) |
| `created_at` | `datetime` | Sí | Fecha de creación |
| `updated_at` | `datetime` | Sí | Fecha de última actualización |
| `profile_picture_url` | `str` | No | URL de foto de perfil |
| `roles` | `list[RoleEnum]` | Sí | Roles del usuario (default: `[user]`) |
| `token_version` | `int` | Sí | Versión del token (invalidación de JWT, default: 0) |
| `google_id` | `str` | No | ID de Google (auth OAuth) |
| `auth_provider` | `AuthProviderEnum` | Sí | Proveedor: `local` o `google` |

### 3.2 Operaciones del repositorio

| Operación | Descripción |
|-----------|-------------|
| `get_by_id(id)` | Busca usuario por `_id` (ObjectId) |
| `get_all()` | Lista todos los usuarios |
| `get_by_username(username)` | Busca por username (case-insensitive) |
| `get_by_email(email)` | Busca por email (case-insensitive) |
| `get_hashed_password(username)` | Proyección solo del campo `hashed_password` |
| `verify_credentials(username, password)` | Verifica credenciales contra hash bcrypt |
| `save(entity)` | Upsert (insert o update) con validación de duplicados |
| `delete(id)` | Elimina usuario por `_id` |
| `get_by_google_id(google_id)` | Busca por ID de Google |
| `link_google_account(user_id, google_id)` | Vincula cuenta Google a usuario existente |
| `add_google_user(...)` | Crea usuario nuevo vía Google (sin contraseña) |

### 3.3 Notas de seguridad

- `hashed_password` **no está en `UserEntity`** (dominio puro). Solo vive en el documento MongoDB y se recupera vía proyección en `get_hashed_password()`.
- `profile_picture_url` almacena una URL externa (no hay subida de archivos nativa).

---

## 4. Colección `solutions` — Canvas / Proyectos

**Archivos:**
- Dominio: `domain/entities/SolutionEntity.py`
- Documento: `infra/persistence/documents/SolutionDocument.py`
- Repositorio: `infra/persistence/repositories/SolutionRepoImpl.py`
- Mapper: `infra/persistence/mappers/SolutionMapper.py`

### 4.1 Esquema del documento MongoDB (`solutions`)

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `_id` | `ObjectId` | Sí | Clave primaria |
| `name` | `str` | Sí | Nombre de la solución (1–200 chars) |
| `user_id` | `str` | Sí | ID del usuario propietario (filtrado de ownership) |
| `last_version_saved` | `str` | Sí | Nombre de la última versión guardada (default: `"unknown"`) |
| `src_img` | `str` | Sí | URL de imagen/captura visual del modelo (default: `"http://unknown.es"`, max 500 chars) |
| `last_updated_at` | `datetime` | No | Fecha de última actualización |
| `versions` | `list` | No | **No se usa** — las versiones viven en colección separada `versions` |

### 4.2 Características clave

- **Ownership por usuario:** Cada solución tiene un `user_id`. El repositorio expone `get_all_for_user(user_id)` que filtra a nivel de base de datos (`find({'user_id': user_id})`), no en Python.
- **Relación con versiones:** La colección `solutions` **no embute** versiones. Las versiones viven en la colección separada `versions`, referenciadas por `solution_id` (string).
- **Campo `src_img`:** Almacena la URL de la captura visual o imagen del modelo. Es solo una cadena de texto — no hay gestión de archivos binarios.

### 4.3 Operaciones del repositorio

| Operación | Descripción |
|-----------|-------------|
| `get_by_id(id)` | Obtiene solución por `_id` (sin versiones) |
| `get_all()` | Lista todas las soluciónes |
| `get_all_for_user(user_id)` | Lista soluciones filtradas por propietario |
| `save(entity)` | Upsert de solución |
| `delete(id)` | Elimina solución por `_id` |

---

## 5. Colección `versions` — Versiones de esquemas JSON

**Archivos:**
- Dominio: `domain/entities/VersionEntity.py`
- Documento: `infra/persistence/documents/VersionDocument.py`
- Repositorio: `infra/persistence/repositories/VersionRepoImpl.py`
- Mapper: `infra/persistence/mappers/VersionMapper.py`

### 5.1 Esquema del documento MongoDB (`versions`)

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `_id` | `ObjectId` | Sí | Clave primaria |
| `submodels` | `list[dict]` | Sí | Esquema JSON del modelo (nodos, aristas, submodelos) |
| `description` | `str` | Sí | Descripción de la versión |
| `solution_id` | `str` | Sí | ID de la solución padre (string, no ObjectId) |

### 5.2 Estructura de `submodels` (JSON anidado)

Cada `submodel` contiene:

```json
{
  "nodes": [
    {
      "id": "string",
      "name": "string",
      "type": "string",
      "position": { "x": float, "y": float },
      "cols": [
        { "id": "string", "name": "string", "type": "string" }
      ],
      "nested_nodes": [ ... recursivo ... ]
    }
  ],
  "edges": [
    {
      "id": "string",
      "source": "string",
      "target": "string",
      "cardinality": "string"  // ej: "1 ... 1"
    }
  ]
}
```

**Value objects de dominio** (en `domain/entities/VersionEntity.py`):

| Clase | Campos | Descripción |
|-------|--------|-------------|
| `Position` | `x: float`, `y: float` | Coordenadas 2D de un nodo en el canvas |
| `Column` | `id`, `name`, `type` | Columna de un nodo o nested node |
| `NestedNode` | `id`, `name`, `cols`, `nested_nodes`, `cardinality` | Nodo anidado recursivo |
| `Node` | `id`, `name`, `type`, `position`, `cols`, `nested_nodes` | Nodo del diagrama con posición |
| `Edge` | `id`, `source`, `target`, `cardinality` | Conexión dirigida entre nodos |
| `Submodel` | `nodes: List[Node]`, `edges: List[Edge]` | Subgrupo lógico de nodos y aristas |
| `VersionEntity` | `id`, `submodels`, `description`, `solution_id` | Entidad completa de versión |

### 5.3 Soporte para múltiples versiones de esquemas

Cada versión es un documento independiente en `versions` con su propio `_id` y `solution_id`. Esto permite:

- **Múltiples versiones por solución:** Una solución puede tener N versiones, cada una con su propio esquema JSON completo.
- **Esquemas independientes:** Cada versión almacena su propio `submodels` (grafo de nodos/aristas) sin afectar a otras versiones.
- **Recuperación por solución:** `get_by_solution_id(solution_id)` devuelve todas las versiones de una solución.
- **Integridad referencial:** Al crear una versión, el repositorio verifica que la solución padre exista en la colección `solutions`.

### 5.4 Operaciones del repositorio

| Operación | Descripción |
|-----------|-------------|
| `get_by_id(id)` | Obtiene versión por `_id` |
| `get_all()` | Lista todas las versiones |
| `get_by_solution_id(solution_id)` | Lista versiones de una solución |
| `get_by_solution_ids(ids)` | Lista versiones de múltiples soluciones (`$in`) |
| `save(entity)` | Upsert con verificación de solución padre |
| `delete(id)` | Elimina versión por `_id` |
| `delete_by_solution_id(solution_id)` | Elimina todas las versiones de una solución |

---

## 6. Colección `queries` — Consultas guardadas

**Archivos:**
- Dominio: `domain/entities/QueryEntity.py`
- Documento: `infra/persistence/documents/QueryDocument.py`
- Repositorio: `infra/persistence/repositories/QueryRepoImpl.py`
- Mapper: `infra/persistence/mappers/QueryMapper.py`

### 6.1 Esquema del documento MongoDB (`queries`)

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `_id` | `ObjectId` | Sí | Clave primaria |
| `full_query` | `str` | Sí | Texto de la consulta (max 10,000 chars) |
| `collections` | `list[str]` | No | Colecciones asociadas |
| `highlighted_words` | `list[str]` | No | Palabras resaltadas |
| `solution_id` | `ObjectId` | Sí | ID de la solución padre (ObjectId, diferente a `versions`) |

**Nota de inconsistencia:** En `queries`, `solution_id` se almacena como `ObjectId`, mientras que en `versions` se almacena como `string`. Esto es una inconsistencia conocida del esquema.

---

## 7. Mappers — Traducción entre capas

Todos los mappers viven en `infra/persistence/mappers/` y son **stateless** (métodos estáticos). Cada uno traduce entre tres formas:

```
Raw MongoDB dict  ↔  Domain Entity  ↔  Presentation DTO
```

| Mapper | Colección | Métodos principales |
|--------|-----------|---------------------|
| `UserMapper` | `users` | `to_entity()`, `from_create_request()`, `from_google_request()`, `to_persistence()`, `to_response()` |
| `SolutionMapper` | `solutions` | `to_entity()`, `from_create_request()`, `to_persistence()`, `to_response()` |
| `VersionMapper` | `versions` | `to_entity()`, `from_create_request()`, `to_persistence()`, `to_response()` |
| `QueryMapper` | `queries` | `to_entity()`, `to_entity_from_dict()`, `to_persistence()`, `to_document()`, `from_create_request()`, `to_response()` |

**Regla:** Cero mapeo inline en repositorios o routers. Todo pasa por el mapper.

---

## 8. Almacenamiento de imágenes / capturas visuales (Storage)

### Estado actual: NO hay servicio de Storage implementado

Tras revisar todo el código fuente (`grep` sobre `storage`, `upload`, `S3`, `bucket`, `cloudinary`, `imgur`, `capture`, `screenshot`, `image`), **no existe ningún servicio de almacenamiento de archivos binarios ni capturas visuales** en el proyecto.

### Cómo se manejan las imágenes actualmente

El campo `src_img` en `SolutionEntity` y `SolutionDocument` es simplemente una **URL string**:

```python
# domain/entities/SolutionEntity.py
src_img: str = "http://unknown.es"  # default

# def update_image(self, src_img: str)
#   - Valida que no esté vacío
#   - Valida que no exceda 500 caracteres
#   - Almacena la URL como string
```

**Flujo actual:**
1. El frontend envía una URL de imagen en el `src_img` del request.
2. El backend la almacena como string en MongoDB (`solutions.src_img`).
3. El backend la devuelve como string en la respuesta HTTP.

### Qué falta (no implementado)

| Aspecto | Estado | Observación |
|---------|--------|-------------|
| Subida de archivos (multipart/form-data) | ❌ No implementado | No hay endpoint de upload |
| Almacenamiento en bucket (S3, Cloudinary, etc.) | ❌ No implementado | No hay integración con ningún proveedor |
| Generación de capturas visuales de modelos | ❌ No implementado | No hay servicio que renderice/escape imágenes de los diagramas |
| CDN / entrega optimizada de imágenes | ❌ No implementado | `src_img` apunta a URL externa opaca |
| Validación de tipo de archivo/imagen | ❌ No implementado | Solo validación de longitud de string |

### Recomendación

Si se necesita un servicio de Storage para capturas visuales de los modelos (canvas/diagramas), se debe implementar una nueva capa de infraestructura, por ejemplo:

```
infra/persistence/storage/
├── storage.py          # Interfaz abstracta (port)
├── s3_storage.py       # Implementación AWS S3
├── local_storage.py    # Implementación local (desarrollo)
└── __init__.py
```

Y crear un caso de uso en `application/use_cases/` para manejar la subida y asociación de imágenes a soluciones.

---

## 9. Índices y consultas

**Estado:** No se crean índices automáticamente en el lifespan de la aplicación. Esto es un hallazgo conocido del reporte de arquitectura (§9.7 del reporte anterior).

Índices mínimos recomendados:
| Colección | Campo | Tipo | Razón |
|-----------|-------|------|-------|
| `users` | `username` | Único | Búsqueda por login, evitar duplicados |
| `users` | `email` | Único | Búsqueda por email, evitar duplicados |
| `users` | `google_id` | Único (sparse) | Auth Google, evitar duplicados |
| `solutions` | `user_id` | No único | Consultas de ownership filtradas |
| `versions` | `solution_id` | No único | Recuperar versiones de una solución |
| `queries` | `solution_id` | No único | Recuperar queries de una solución |

Sin índices, todas las consultas son **collection scans** y los handlers de `DuplicateKeyError` en `UserRepoImpl` son código muerto (no hay índices únicos que los disparen).

---

## 10. Conclusión

La persistencia de Qolqa en MongoDB está bien estructurada con separación clara entre:
- **Domain:** Entidades puras sin dependencias de infraestructura
- **Application:** Use cases y DTOs de aplicación
- **Infrastructure Persistence:** Documentos MongoDB, mappers, repositorios Motor

Las cuatro colecciones (`users`, `solutions`, `versions`, `queries`) cubren el modelo de datos completo para usuarios, proyectos/canvas, versiones de esquemas JSON y consultas.

**Brecha importante:** No existe ningún servicio de Storage para archivos binarios ni capturas visuales. El campo `src_img` es solo una URL string externa. Si se requiere subida y gestión de imágenes, debe construirse esa capa de infraestructura desde cero.

---