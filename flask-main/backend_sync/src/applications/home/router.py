from flask import make_response
from flask.views import MethodView
from flask_smorest import Blueprint

blp = Blueprint("home", "home", url_prefix="", description="Landing y health-check")

HTML = """<!doctype html><html lang="es"><meta charset="utf-8">
<title>API de Modelos</title><main><h1>API de Modelos</h1>
<p>Servicio Flask disponible.</p><a href="/docs">Documentación OpenAPI</a></main></html>"""


@blp.route("/")
class Home(MethodView):
    def get(self):
        return make_response(HTML, 200, {"Content-Type": "text/html; charset=utf-8"})


@blp.route("/health")
class Health(MethodView):
    def get(self):
        return {"status": "ok"}
