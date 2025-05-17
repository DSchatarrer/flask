# src\routers\login.py

from flask.views import MethodView
from flask_smorest import Blueprint

try:
    from src.core.manager_db import require_db_session
    from src.controllers.login_service import LoginService
    from src.schemas.login_schema import LoginResponseSchema,LoginRequestSchema
except ImportError:
    from core.manager_db import require_db_session
    from controllers.login_service import LoginService
    from schemas.login_schema import LoginResponseSchema,LoginRequestSchema

blp = Blueprint(
    "login", "login",
    url_prefix="/login",
    description="login",
)

@blp.route("/")
class Login(MethodView):
    @blp.arguments(LoginRequestSchema)
    @blp.response(200, LoginResponseSchema)
    @blp.response(401, description="Credenciales incorrectas")
    @blp.response(404, description="Usuario no encontrado")
    @blp.response(400, description="Campos inválidos")
    @require_db_session
    def post(self, credentials, *, db):
        """
        Login de usuario: se espera JSON con user y password
        """
        return LoginService(db).login(credentials.get("user"), 
                                      credentials.get("password"))
    

@blp.route("/register")
class RegisterUser(MethodView):
    @blp.arguments(LoginRequestSchema)
    @blp.response(200, LoginResponseSchema)
    @require_db_session
    def post(self, credentials, *, db):
        """
        Crea un usuario si no existe
        """
        return LoginService(db).create_user(credentials.get("user"), 
                                            credentials.get("password"), 
                                            credentials.get("role"))
