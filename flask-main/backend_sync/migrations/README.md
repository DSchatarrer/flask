- Base de datos nueva: `alembic upgrade head`.
- Base de datos existente: haz backup y compara primero el esquema con la baseline.
  Si coincide exactamente y SOLO entonces, marca la revisión como aplicada con `alembic stamp 20261027_01`.
- No apliques `upgrade` sobre tablas antiguas ya presentes sin revisar; puede fallar con `table already exists`.
- Para modificaciones posteriores: `alembic revision --autogenerate -m "..."` y revisa el resultado manualmente.
- Evita usar `flask init-db` como migración en producción.
