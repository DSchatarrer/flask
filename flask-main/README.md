# Flask asíncrono — mismo árbol modular

Partiendo del último ZIP entregado `flask-estructura-fastapi-tipado-corregido.zip`, el proyecto resultante se organiza como:

```text
flask-async-main/
└── backend_async/
    ├── src/
    │   ├── main.py             # Factoría Flask
    │   ├── asgi.py             # Adaptador ASGI con WsgiToAsgi
    │   ├── applications/
    │   │   ├── home/router.py
    │   │   ├── login/{router,controller,schemas}.py
    │   │   └── users/{router,controller,schemas}.py
    │   ├── core/
    │   │   ├── manager_db.py   # AsyncEngine, async_sessionmaker y dependencias
    │   │   ├── security.py     # Guards async de sesión/JWT/roles
    │   │   ├── session_cleanup.py
    │   │   ├── commands.py     # CLI lanza I/O async
    │   │   ├── models/
    │   │   └── settings.py
    │   └── scripts/
    ├── migrations/
    ├── tests/
    └── validation/
```

**Flask no pasa a ser un ASGI nativo**, aunque la lógica HTTP/BD de este proyecto utilice asyncio y se distribuya con un adaptador ASGI. Consulta `backend_async/README.md` para instalación, detalles y limitaciones.
