# src/routers/home.py

from flask.views import MethodView
from flask_smorest import Blueprint
from flask import make_response

blp = Blueprint(
    "home", "home",
    url_prefix="",
    description="Landing y health-check",
)

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>API de Modelos</title>
  <style>
    body{font-family:sans-serif;display:flex;align-items:center;
         justify-content:center;flex-direction:column;height:100vh;margin:0}
    h1{font-size:2.5rem;margin-bottom:.5rem}
    p{font-size:1.1rem;margin:.2rem 0}
    a{color:#2563eb;text-decoration:none;font-weight:600}
    a:hover{text-decoration:underline}
  </style>
</head>
<body>
  <h1>🚀 API de Modelos</h1>
  <p>Bienvenido. Todo funciona correctamente.</p>
  <p><a href="/docs">Explorar documentación OpenAPI</a></p>
  <p><a href="/users">Probar endpoint de usuarios</a></p>
</body>
</html>
"""

@blp.route("/")
class Home(MethodView):
    """Página principal y health-check."""
    def get(self):
        return make_response(HTML, 200, {"Content-Type": "text/html"})
