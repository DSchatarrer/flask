"""Uso: python -m src.scripts.cleanup_expired_sessions --retention-days 7."""
from src.core.commands import cleanup_sessions_command
from src.main import create_app


def main():
    app = create_app()
    with app.app_context():
        cleanup_sessions_command.main(standalone_mode=True)


if __name__ == "__main__":
    main()
