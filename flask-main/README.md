# Flask — Estructura de carpetas equivalente al proyecto FastAPI

El proyecto Flask original se conserva funcionalmente sin refactorizar la lógica.
**Solo cambia la organización en el ZIP**: al igual que `fastapi-main/backend_async/`,
este archivo se distribuye como `flask-main/backend_sync/`.

## Correspondencia

| FastAPI original | Flask reorganizado |
| --- | --- |
| `fastapi-main/backend_async/src/main.py` | `flask-main/backend_sync/src/main.py` |
| `backend_async/src/applications/<dominio>/router.py` | `backend_sync/src/applications/<dominio>/router.py` |
| `backend_async/src/applications/<dominio>/controller.py` | `backend_sync/src/applications/<dominio>/controller.py` |
| `backend_async/src/applications/<dominio>/schemas.py` | `backend_sync/src/applications/<dominio>/schemas.py` |
| `backend_async/src/core/models/` | `backend_sync/src/core/models/` |
| `backend_async/src/core/security.py` | `backend_sync/src/core/security.py` |
| `backend_async/src/scripts/` | `backend_sync/src/scripts/` |
| `backend_async/tests/` | `backend_sync/tests/` |

Los dominios (`home`, `login`, `users` en Flask) conservan su identidad. No tendría
sentido renombrarlos a `pacientes` o `info_errores`, que son funciones distintas
incluidas en el ejemplo FastAPI. `core/manager_db.py` tampoco se renombra a
`manager_db_async.py`: Flask utiliza sesiones SQLAlchemy síncronas.

## Ejecución (desde la carpeta backend_sync)

```bash
cd flask-main/backend_sync
python -m venv .venv
# Activar el entorno virtual según el sistema operativo
pip install -r requirements-dev.txt
# Copiar .env.example a .env y cambiar los secretos
flask --app src.main:create_app run
python -m pytest -q tests validation
```

La aplicación conserva el mismo punto de entrada `src.main:create_app` y el
resto de comandos originales (por ejemplo `create-admin`, `cleanup-sessions`).
Para más instrucciones, lee `backend_sync/README.md`.

## Alcance de la adaptación

- Los contenidos de los ficheros originales, incluido **todo el código Python**,
  **permanecen idénticos byte a byte**.
- No se modifican rutas, Blueprints, controladores, schemas, migraciones,
  inyección de sesiones, autenticación ni configuración.
- Solo se añade este documento de orientación y una carpeta contenedora
  `backend_sync/` para coincidir con la presentación de `fastapi-main.zip`.

Fuentes: documentaciones oficiales de FastAPI ("Bigger Applications") y Flask
("Modular Applications with Blueprints" y "Application Factories").
