"""Entrada ASGI compatible para desplegar Flask en Hypercorn o Uvicorn.

Flask permanece WSGI internamente. WsgiToAsgi mantiene un event loop persistente.
"""
from asgiref.wsgi import WsgiToAsgi

from src.main import create_app

app = create_app()
asgi_app = WsgiToAsgi(app)
