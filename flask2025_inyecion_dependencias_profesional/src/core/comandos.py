# src/core/comandos.py

import click
from flask.cli import with_appcontext

try:
    from src.core.manager_db import init_db
except ImportError:
    from core.manager_db import init_db


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Crear/actualizar las tablas en la base de datos."""
    init_db()
    click.echo("✔ Base de datos inicializada.")


def register_commands(app):
    """
    Registra todos los comandos en la instancia de Flask.

    Llama a esta función desde create_app().
    """
    app.cli.add_command(init_db_command)

    # Aquí puedes ir añadiendo otros comandos en el futuro
    # app.cli.add_command(otro_comando)
