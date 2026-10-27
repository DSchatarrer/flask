# Backend Flask modernizado (arquitectura equivalente a la skill FastAPI)

Refactor de `flask2025_inyecion_dependencias_profesional.zip` **basado en los archivos entregados**.

## Estructura

```text
src/
├── main.py                         # create_app, Flask-Smorest, Blueprints
├── core/
│   ├── settings.py                 # Settings (cacheable)
│   ├── manager_db.py               # Engine/SessionLocal POR APP; Session por petición
│   ├── security.py                 # require_auth, require_role, require_secret_param (solo validación)
│   ├── session_cleanup.py          # DELETE de sesiones expiradas sin HTTP
│   ├── commands.py                 # CLI init-db, create-admin, cleanup-sessions
│   └── models/
│       ├── base.py                 # DeclarativeBase
│       ├── users.py                # SQLAlchemy Users; tabla usuarios
│       └── sessions.py             # SQLAlchemy Sessions; tabla sesiones
├── applications/
│   ├── home/router.py              # GET / y GET /health
│   ├── login/
│   │   ├── router.py              # POST /login/ y POST /login/register
│   │   ├── controller.py          # gestión login/alta
│   │   └── schemas.py             # Marshmallow (no Pydantic/SQLModel)
│   └── users/
│       ├── router.py              # GET /users/users (conservada)
│       ├── controller.py          # lógica de presentación
│       └── schemas.py
└── scripts/cleanup_expired_sessions.py  # cron fuera del request
migrations/                       # baseline Alembic
requirements*.txt
.env.example
tests/
```

## Instalación (Python 3.12+)

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
cp .env.example .env               # Windows: copy .env.example .env
# CAMBIA TODOS los secretos de .env y ajusta DATABASE_URL/COOKIE_SECURE.
flask --app src.main:create_app init-db   # solo BD vacía / desarrollo
flask --app src.main:create_app create-admin --username admin
flask --app src.main:create_app run --debug
```

**En producción**, con BD nueva: `alembic upgrade head`; con BD existente revisar primero
`migrations/README.md`. No uses `create_all` para migrar esquemas existentes.
Para PostgreSQL configura `DATABASE_URL=postgresql+psycopg2://...` o
`DATASOURCE_*`; para pruebas SQLite. MySQL requiere driver propio (ej. pymysql)
y pruebas específicas. Ningún modelo importa el dialecto PostgreSQL.

## Sesiones y roles

`require_auth()` valida el JWT y comprueba `sesiones.exp` en cada petición **sin borrar**.
`require_role("admin")` compara el rol en `usuarios` sin escrituras. No existe
expiración de roles en estos modelos; solo expiran **sesiones** de usuario.
Un programador externo, no Flask, debe ejecutar la limpieza periódica:

```bash
flask --app src.main:create_app cleanup-sessions --retention-days 7
# o python -m src.scripts.cleanup_expired_sessions --retention-days 7
```

**Rutas conservadas**: `POST /login/`, `POST /login/register`, `GET /users/users`, `GET /`.
Se añade `GET /health`. La cookie sigue llamándose `X-Sync.Ref`.

**Cambios intencionados de seguridad:** `/login/register` ahora exige una cookie
válida y rol `admin`. Crea el primer admin con `create-admin`. Login erróneo
responde 401 de forma uniforme; `/users/users` devuelve un saludo con el nombre
(no refleja un JWT secreto). Preferentemente envía la API key en el header
`X-API-Key`; `?apikey=` sigue aceptándose por compatibilidad, pero puede quedar
registrado en logs. En HTTP local usa `COOKIE_SECURE=false`; en producción HTTPS
mantén `COOKIE_SECURE=true`. Ajusta CORS a orígenes concretos, jamás `*` con cookies.

## Transacciones e inyección

`configure_database(app)` crea un engine y un `sessionmaker` una vez **por instancia
de Flask**, registrado en `app.extensions`. Cada ruta obtiene una sesión propia
con `@require_db_session`, que garantiza cierre y rollback ante excepciones.
La transacción de escritura hace `db.commit()` explícito en `LoginController`;
CLI hace `with session_factory.begin()` para commit/rollback automático.
La configuración usa `lru_cache(maxsize=1)`; las sesiones **nunca** se cachean.
El `engine` vive mientras lo hace el proceso/app (no se desecha en `teardown_appcontext`
porque se ejecuta al final de cada request).

Flask es WSGI: no hemos convertido artificialmente los handlers a `async def`.
Para un backend enteramente asíncrono con `AsyncSession`, FastAPI/ASGI suele
resultar más coherente.

## Tests

```bash
pytest -q
python -m compileall -q src tests migrations
```

**No incluidos**: secretos, credenciales reales ni conexión a BD de producción.
**Pendiente de seguridad para producción**: añade protección CSRF a mutaciones
basadas en cookies, limitación de intentos de login, comprobación de seguridad
de los roles permitidos al registrar y auditoría de accesos.
