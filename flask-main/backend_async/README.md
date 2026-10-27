# Flask con lógica y base de datos asíncronas

Conversión del proyecto **`flask-estructura-fastapi-tipado-corregido.zip`** (última entrega Flask) manteniendo estructura modular, Flask-Smorest y reglas de negocio. No es una migración a FastAPI ni a Quart.

> **Limitación importante:** Flask sigue siendo **WSGI**, incluso usando `async def`. Esta versión convierte **el código de aplicación y el acceso a datos** a async y ofrece un adaptador ASGI; **no convierte Flask en un framework ASGI nativo**. Para ASGI puro y mayor concurrencia HTTP, utilizar Quart o FastAPI requiere una migración de framework. Fuente: https://flask.palletsprojects.com/en/stable/async-await/

## Instalación

Python 3.12+ recomendado. Desde `backend_async/`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
# Edita .env: secretos únicos y DATABASE_URL adecuado.
flask --app src.main:create_app init-db
flask --app src.main:create_app create-admin --username admin
hypercorn src.asgi:asgi_app --bind 127.0.0.1:5000
```

Linux/macOS: `source .venv/bin/activate` y `cp .env.example .env`.

Puedes arrancar también con `flask --app src.main:create_app run`, pero ese servidor es de desarrollo WSGI. El servidor `hypercorn` usa el adaptador `WsgiToAsgi`, no ASGI nativo.

Para PostgreSQL usa `DATABASE_URL=postgresql+asyncpg://usuario:contraseña@servidor:5432/bd`. Para SQLite local, `DATABASE_URL=sqlite+aiosqlite:///local.db`. Se normalizan los drivers síncronos antiguos `psycopg2` y `pysqlite` a `asyncpg` y `aiosqlite` cuando aparecen en DATABASE_URL; se rechazan los dialectos no soportados. `DATASOURCE_*` construye automáticamente la URL de `asyncpg`.

## Correspondencias con la versión síncrona

| Antes | Ahora |
| --- | --- |
| `create_engine` | `create_async_engine` |
| `sessionmaker(Session)` | `async_sessionmaker(AsyncSession)` |
| `with get_session() as db` | `async with get_session() as db` |
| `db.get`, `db.execute` | `await db.get`, `await db.execute` |
| `db.commit`, `db.rollback` | `await db.commit`, `await db.rollback` |
| `with engine.connect()` | `async with engine.connect()` |
| `Base.metadata.create_all(engine)` | `await connection.run_sync(Base.metadata.create_all)` |
| `def post(self, ...)` | `async def post(self, ...)` |
| `def cleanup_expired_sessions` | `async def cleanup_expired_sessions` |

`create_app()`, Click y el generador de la API OpenAPI siguen siendo síncronos porque Flask/Click hacen inicialización síncrona; eso no introduce operaciones de BD bloqueantes en peticiones. Se usa `asyncio.run` **solo en comandos CLI síncronos**, nunca dentro de una vista. El trabajo de hashing de contraseñas se ejecuta con `asyncio.to_thread` para no bloquear el loop HTTP.

`NullPool` en `manager_db.py` impide reutilizar conexiones entre distintos bucles de eventos, algo que puede ocurrir en WSGI, CLI y tests. En una implementación exclusiva bajo ASGI podrías medir y configurar pooling, respetando el ciclo de vida del engine.

## Rutas y semántica conservadas

- `GET /`, `GET /health`, `POST /login/`, `POST /login/register`, `GET /users/users`.
- Cookie de autenticación `X-Sync.Ref`, JWT con sesiones persistidas, autorización por rol `admin` para registros y secret header `X-API-Key`.
- Compatibilidad con `?apikey=` **solo para clientes legados**. No usar en nuevas rutas: las URLs acaban en logs.
- Controllers hacen `commit()` explícito; dependencias cierran y revierten en excepciones; CLI usa `async with factory.begin()`.
- Limpieza fuera de HTTP, mediante `flask --app src.main:create_app cleanup-sessions --retention-days 7`.
- Modelos/tablas `usuarios`, `sesiones` sin cambios; migración Alembic baseline idéntica y `env.py` actualizado a async.

## Producción y seguridad

Usar `alembic upgrade head` **solo para BD nueva**; si la BD existe, comparar el esquema y consultar `migrations/README.md` antes de `stamp` o `upgrade`. Nunca ejecutar `create_all` para migraciones productivas.

No se han añadido protecciones CSRF, rate limiting ni nuevas reglas de roles, porque la petición era migrar I/O sin alterar contratos. **Son tareas pendientes antes de producción**, especialmente si usas cookies de autenticación.

Al usar SQLite, `aiosqlite` delega a hilos; las consultas son compatibles con API async, pero no es I/O de red asíncrono nativo. Para PostgreSQL `asyncpg` sí utiliza I/O asíncrono.

## Tests y alcance de verificación

```powershell
python -m pytest -q tests validation
python -m compileall -q src tests migrations validation
```

Las pruebas de integración de `tests/` precisan instalar Flask, Flask-Smorest, aiosqlite, etc. Las pruebas `validation/` comprueban esquema, contratos async, migraciones y sintaxis sin esas dependencias. En el entorno en el que se generó el ZIP pasaron **11/11** tests de `validation`, pero no se pudieron ejecutar pruebas HTTP por imposibilidad de instalar dependencias externas. Se recomienda comprobar el recorrido login → registro admin → endpoint protegido con SQLite y luego PostgreSQL real.

Referencias: https://flask.palletsprojects.com/en/stable/async-await/ , https://flask.palletsprojects.com/en/stable/deploying/asgi/ , https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html , https://alembic.sqlalchemy.org/en/latest/cookbook.html
