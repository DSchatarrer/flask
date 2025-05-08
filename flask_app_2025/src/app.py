# src/app.py

from flask import Flask
from flask_smorest import Api
from flask_cors import CORS
import tensorflow as tf

try:
    from src.core.manager_db import init_db
except:
    from core.manager_db import init_db

def create_app():
    app = Flask(__name__)
    app.secret_key = "una-clave-ultra-secreta"

    CORS(app, resources={r"/*": {"origins": "*"}})

    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "API de Modelos"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    api = Api(app)

    # init_db()

    try:
        curie_net = tf.keras.models.load_model("./src/dnn/mi_modelo_vgg16/")
        # pierre_net = tf.keras.models.load_model("./src/dnn/mi_modelo_vgg16-tubos/")
    except:
        curie_net = tf.keras.models.load_model("./dnn/mi_modelo_vgg16/")
        # pierre_net = tf.keras.models.load_model("./dnn/mi_modelo_vgg16-tubos/")

    app.config["curie_net"] = curie_net
    app.config["pierre_net"] = "pierre_net"


    try:
        from src.routes.models_routes import blp as models_blp
        from src.routes.inference_routers import blp as inference_blp
        from src.routes.inference_routers import blp as inference_blp, web_predict_bp
    except:
        from routes.models_routes import blp as models_blp
        from routes.inference_routers import blp as inference_blp
        from routes.inference_routers import blp as inference_blp, web_predict_bp

    api.register_blueprint(models_blp)
    api.register_blueprint(inference_blp)
    app.register_blueprint(web_predict_bp)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
