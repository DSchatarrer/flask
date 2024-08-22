from flask import Flask, jsonify
from flask_azure_oauth import FlaskAzureOauth

app = Flask(__name__)

# Configuración de Azure AD
app.config['AZURE_OAUTH_TENANCY'] = 'tu-tenant-id'
app.config['AZURE_OAUTH_APPLICATION_ID'] = 'tu-application-id'

# Inicializa Flask-Azure-OAuth
auth = FlaskAzureOauth()
auth.init_app(app)

@app.route('/unprotected')
def unprotected():
    return 'Esta es una ruta sin protección.'

@app.route('/protected')
@auth()
def protected():
    return 'Esta es una ruta protegida, solo usuarios autenticados pueden acceder.'

@app.route('/protected-with-single-scope')
@auth('required-scope')
def protected_with_scope():
    return 'Esta es una ruta protegida con un scope específico.'

@app.route('/protected-with-multiple-scopes')
@auth('scope1 scope2')
def protected_with_multiple_scopes():
    return 'Esta es una ruta protegida que requiere múltiples scopes.'
