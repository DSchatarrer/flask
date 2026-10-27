from flask import g
from flask.views import MethodView
from flask_smorest import Blueprint

from src.applications.users.controller import UsersController
from src.applications.users.schemas import GreetingSchema
from src.core.manager_db import require_db_session
from src.core.security import require_auth, require_secret_param

blp = Blueprint("users", "users", url_prefix="/users", description="Operaciones con usuarios")


@blp.route("/users")  # URL legado conservada: GET /users/users
class DemoData(MethodView):
    @blp.doc(security=[{"CookieAuth": [], "ApiKeyAuth": []}])
    @blp.response(200, GreetingSchema)
    @require_db_session
    @require_auth()
    @require_secret_param(param_name="apikey", header_name="X-API-Key")
    def get(self, *, db):
        return UsersController().greet(g.current_user.usu)
