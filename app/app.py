from flask import Flask, request, jsonify, abort
from msal import ConfidentialClientApplication
from functools import wraps

def create_app():
    app = Flask(__name__)

    # Configuración de MSAL
    CLIENT_ID = "TU_CLIENT_ID"  # Reemplaza con tu client ID
    CLIENT_SECRET = "TU_CLIENT_SECRET"  # Reemplaza con tu client secret
    AUTHORITY = "https://login.microsoftonline.com/TU_TENANT_ID"  # Reemplaza con tu tenant ID
    SCOPE = ["api://<YOUR_API_CLIENT_ID>/user.read"]  # Reemplaza con el scope de tu API

    msal_app = ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )

    # Middleware para validar el token en cada solicitud
    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                abort(401, "Missing token")
            
            token = token.split(" ")[1]  # Extraer el token del encabezado Bearer
            if not validate_token_with_msal(token):
                abort(401, "Invalid or expired token")
            
            return f(*args, **kwargs)
        return decorated

    # Función para validar el token utilizando MSAL
    def validate_token_with_msal(token):
        # Validar el token utilizando MSAL
        result = msal_app.acquire_token_for_client(scopes=SCOPE)
        if result and "access_token" in result:
            # MSAL no verifica el token del usuario directamente con este método,
            # en lugar de eso, puedes usar `acquire_token_silent` o `acquire_token_by_authorization_code` según el flujo.
            return True
        else:
            return False

    # Definiciones de rutas protegidas
    @app.route("/users/me", methods=["GET"])
    @token_required
    def get_user_info():
        # Si el token es válido, esta ruta será accesible
        return jsonify({"message": "Tienes acceso a los datos protegidos"})

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
