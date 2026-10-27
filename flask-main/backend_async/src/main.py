"""Application factory. No crea tablas ni ejecuta limpieza en peticiones."""
from typing import Any, Mapping

from flask import Flask
from flask_cors import CORS
from flask_smorest import Api

from src.core.commands import register_commands
from src.core.manager_db import configure_database
from src.core.settings import Settings, get_settings


def create_app(settings: Settings | None = None, test_config: Mapping[str, Any] | None = None) -> Flask:
    config = settings or get_settings()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=config.FLASK_SECRET_KEY,
        JWT_SECRET_KEY=config.JWT_SECRET_KEY,
        JWT_ALGORITHM=config.ALGORITHM,
        TOKEN_SECONDS_EXP=config.TOKEN_SECONDS_EXP,
        API_KEY=config.API_KEY,
        SQLALCHEMY_DATABASE_URI=config.sqlalchemy_database_uri,
        COOKIE_SECURE=config.COOKIE_SECURE,
        BACKEND_CORS_ORIGINS=config.BACKEND_CORS_ORIGINS,
        API_TITLE="API de Modelos",
        API_VERSION="v1",
        OPENAPI_VERSION="3.0.3",
        OPENAPI_URL_PREFIX="/",
        OPENAPI_SWAGGER_UI_PATH="/docs",
        OPENAPI_SWAGGER_UI_URL="https://cdn.jsdelivr.net/npm/swagger-ui-dist/",
    )
    if test_config:
        app.config.update(test_config)

    # CORS desactivado por defecto. Una cookie no debe habilitarse con origen '*'.
    if app.config["BACKEND_CORS_ORIGINS"]:
        CORS(app, resources={r"/*": {"origins": app.config["BACKEND_CORS_ORIGINS"]}}, supports_credentials=True)

    configure_database(app)
    api = Api(app)
    api.spec.components.security_scheme(
        "ApiKeyAuth", {"type": "apiKey", "in": "header", "name": "X-API-Key"}
    )
    api.spec.components.security_scheme(
        "CookieAuth", {"type": "apiKey", "in": "cookie", "name": "X-Sync.Ref"}
    )

    from src.applications.home.router import blp as home_blp
    from src.applications.login.router import blp as login_blp
    from src.applications.users.router import blp as users_blp

    api.register_blueprint(home_blp)
    api.register_blueprint(login_blp)
    api.register_blueprint(users_blp)
    register_commands(app)
    return app


if __name__ == "__main__":
    settings = get_settings()
    create_app(settings).run(
        host=settings.FLASK_RUN_HOST,
        port=settings.FLASK_RUN_PORT,
        debug=settings.FLASK_DEBUG,
    )
