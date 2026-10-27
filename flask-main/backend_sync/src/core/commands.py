"""Comandos de mantenimiento, bootstrap y migraciones. No se ejecutan por HTTP."""
import click
from flask import current_app
from flask.cli import with_appcontext
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from src.core.manager_db import get_session_factory, init_db
from src.core.models.users import Users
from src.core.session_cleanup import cleanup_expired_sessions


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Crear tablas en desarrollo; usar Alembic en producción."""
    init_db()
    click.echo("Base de datos inicializada (solo bootstrap/desarrollo).")


@click.command("create-admin")
@click.option("--username", prompt=True)
@click.password_option()
@with_appcontext
def create_admin_command(username: str, password: str):
    """Crear el primer admin fuera de HTTP, evitando registro público privilegiado."""
    try:
        with get_session_factory().begin() as db:
            if db.get(Users, username):
                raise click.ClickException("El usuario ya existe")
            db.add(Users(usu=username, hash_pwd=generate_password_hash(password), role="admin"))
    except IntegrityError as exc:
        raise click.ClickException("El usuario ya existe") from exc
    click.echo("Administrador creado")


@click.command("cleanup-sessions")
@click.option("--retention-days", type=click.IntRange(min=0), default=7, show_default=True)
@with_appcontext
def cleanup_sessions_command(retention_days: int):
    """Elimina sesiones expiradas con transacción propia (invocar vía cron)."""
    with get_session_factory().begin() as db:
        removed = cleanup_expired_sessions(db, retention_days=retention_days)
    click.echo(f"Sesiones expiradas eliminadas: {removed}")


def register_commands(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(cleanup_sessions_command)
