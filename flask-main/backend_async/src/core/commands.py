"""Comandos Flask/Click síncronos que ejecutan I/O asíncrono en un loop CLI."""
import asyncio

import click
from flask.cli import with_appcontext
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from src.core.manager_db import get_session_factory, init_db
from src.core.models.users import Users
from src.core.session_cleanup import cleanup_expired_sessions


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Crear tablas solo en BD nueva / desarrollo."""
    asyncio.run(init_db())
    click.echo("Base de datos inicializada (solo bootstrap/desarrollo).")


async def _create_admin(username: str, password: str) -> None:
    factory = get_session_factory()
    try:
        async with factory.begin() as db:
            if await db.get(Users, username):
                raise click.ClickException("El usuario ya existe")
            hashed_password = await asyncio.to_thread(generate_password_hash, password)
            db.add(Users(usu=username, hash_pwd=hashed_password, role="admin"))
    except IntegrityError as exc:
        raise click.ClickException("El usuario ya existe") from exc


@click.command("create-admin")
@click.option("--username", prompt=True)
@click.password_option()
@with_appcontext
def create_admin_command(username: str, password: str):
    """Bootstrap de administración sin endpoint público."""
    asyncio.run(_create_admin(username, password))
    click.echo("Administrador creado")


async def _cleanup_sessions(retention_days: int) -> int:
    factory = get_session_factory()
    async with factory.begin() as db:
        return await cleanup_expired_sessions(db, retention_days=retention_days)


@click.command("cleanup-sessions")
@click.option("--retention-days", type=click.IntRange(min=0), default=7, show_default=True)
@with_appcontext
def cleanup_sessions_command(retention_days: int):
    """Limpieza periódica independiente de peticiones HTTP."""
    removed = asyncio.run(_cleanup_sessions(retention_days))
    click.echo(f"Sesiones expiradas eliminadas: {removed}")


def register_commands(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(cleanup_sessions_command)
