"""Protocolo HTTP, cookies y mapeo de excepciones; negocio en controller."""
from flask import current_app, jsonify, make_response
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from src.applications.login.controller import LoginController, InvalidCredentials, UserAlreadyExists
from src.applications.login.schemas import LoginRequestSchema, RegisterRequestSchema, MessageSchema
from src.core.manager_db import require_db_session
from src.core.security import require_auth, require_role

blp = Blueprint("login", "login", url_prefix="/login", description="Autenticación")


@blp.route("/")
class Login(MethodView):
    @blp.arguments(LoginRequestSchema)
    @blp.response(200, MessageSchema)
    @blp.alt_response(401, description="Credenciales incorrectas")
    @require_db_session
    def post(self, credentials, *, db):
        try:
            token = LoginController(db).login(credentials["user"], credentials["password"])
        except InvalidCredentials:
            abort(401, message="Credenciales incorrectas")
        resp = make_response(jsonify({"message": "Login correcto"}), 200)
        resp.set_cookie(
            "X-Sync.Ref", token, max_age=current_app.config["TOKEN_SECONDS_EXP"],
            httponly=True, secure=current_app.config["COOKIE_SECURE"], samesite="Lax", path="/",
        )
        return resp


@blp.route("/register")
class RegisterUser(MethodView):
    @blp.doc(security=[{"CookieAuth": []}])
    @blp.arguments(RegisterRequestSchema)
    @blp.response(201, MessageSchema)
    @blp.alt_response(401, description="Autenticación requerida")
    @blp.alt_response(403, description="Solo administradores")
    @blp.alt_response(409, description="Usuario duplicado")
    @require_db_session
    @require_auth()
    @require_role("admin")
    def post(self, credentials, *, db):
        try:
            LoginController(db).create_user(
                credentials["user"], credentials["password"], credentials["role"]
            )
        except UserAlreadyExists:
            abort(409, message="El usuario ya existe")
        return {"message": "Usuario creado"}
