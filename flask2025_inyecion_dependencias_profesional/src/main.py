# src\main.py

from flask import Flask
from flask_smorest import Api
from flask_cors import CORS

try:
    from src.core.settings import settings
    from src.core.comandos import register_commands
except ImportError:
    from core.settings import settings
    from core.comandos import register_commands

def create_app():
    app = Flask(__name__)

    CORS(app, resources={r"/*": {"origins": "*"}})

    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "API de Modelos"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    api = Api(app)
    api.spec.components.security_scheme(
        "ApiKeyAuth",
        {
            "type": "apiKey",
            "in": "query",          # "header" si la envías en header
            "name": "apikey"
        }
    )
    
    try:
        from src.routers.users import blp as users_blp
        from src.routers.home import blp as home_blp
        from src.routers.login import blp as login_blp
    except:
        from routers.users import blp as users_blp
        from routers.home import blp as home_blp
        from routers.login import blp as login_blp

    api.register_blueprint(home_blp)
    api.register_blueprint(login_blp)
    api.register_blueprint(users_blp)
    
    register_commands(app)
    
    return app

app = create_app()

if __name__ == "__main__":
    app.run(
        host=settings.FLASK_RUN_HOST,
        port=settings.FLASK_RUN_PORT,
        debug=settings.FLASK_DEBUG
    )

