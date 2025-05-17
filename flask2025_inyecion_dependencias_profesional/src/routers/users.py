# src\routers\users.py

from flask.views import MethodView
from flask_smorest import Blueprint
import json
from flask import request

try:
    from src.core.securitry import require_auth, require_secret_param
    from src.core.manager_db import require_db_session
    from src.controllers.demo_data_service import DemoDataService
except ImportError:
    from core.securitry import require_auth, require_secret_param
    from core.manager_db import require_db_session
    from controllers.demo_data_service import DemoDataService

    
blp = Blueprint(
    "users", "users",
    url_prefix="/users",
    description="Operaciones con modelos",
)


@blp.route("/users")
class DemoData(MethodView):
    @blp.doc(security=[{"ApiKeyAuth": []}])
    @blp.response(200)
    @require_db_session
    # @require_auth(roles=("admin",)) 
    @require_auth()
    @require_secret_param(param_name="apikey")
    def get(self, *, db):
        """Listar todos los registros de demo_data"""
        return DemoDataService(db).saludar(request)
