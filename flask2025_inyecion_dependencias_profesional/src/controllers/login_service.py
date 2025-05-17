# src\controllers\login_service.py

from werkzeug.security import check_password_hash, generate_password_hash
from flask_smorest import abort
from flask import make_response, jsonify


try:
    from src.core.settings import settings
    from src.models.users import Users
    from src.models.sessions import Sessions
    from src.core.securitry import create_token, get_uuid_and_exp_from_token
except ImportError:
    from core.settings import settings
    from models.users import Users
    from models.sessions import Sessions
    from core.securitry import create_token, get_uuid_and_exp_from_token


class LoginService:
    def __init__(self, session):
        self.session = session

    def login(self, username: str, password: str):
        if not username or not password:
            abort(400, message="Faltan campos 'user' o 'password'")

        user = self.get_user(username)

        if not user:
            abort(404, message="Usuario no encontrado")

        if not user.hash_pwd or not self.authenticate_user(user.hash_pwd, password):
            abort(401, message="Contraseña incorrecta")
            
        access_token = create_token()
        uuid, exp = get_uuid_and_exp_from_token(access_token)
        
        nueva_sesion = Sessions(token=uuid,usu=username,exp=exp)
        self.session.add(nueva_sesion)
        self.session.commit()
        self.session.refresh(nueva_sesion) 

        resp = make_response(jsonify(message="Login correcto"), 200)
        resp.set_cookie(
            key="X-Sync.Ref",
            value=access_token,
            max_age=settings.TOKEN_SECONDS_EXP,
            httponly=True,
            samesite="Lax",
            path="/"          # o tu subruta específica
            # secure=True      # ponlo en producción si sirves por HTTPS
        )
        return resp
    
    def get_user(self, username: str):
        """
        Devuelve el objeto usuario si existe, o None si no.
        """
        return self.session.query(Users).filter(Users.usu == username).first()
    
    def create_user(self, username: str, password: str, role: str):
        """
        Crea un usuario nuevo si no existe ya. Devuelve el usuario.
        """
        user = self.get_user(username)
        if user:
            return {"message": f"usuario {user.usu} ya existe"}, 200

        hashed_pwd = generate_password_hash(password)
        user = Users(usu=username, hash_pwd=hashed_pwd, role=role)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user) 
        return {"message": f"usuario {user.usu} creado exitosamente"}, 201
    
    def authenticate_user(self, hashed_password: str, plain_password: str) -> bool:
        """
        Verifica si la contraseña en texto plano coincide con el hash.
        """
        return check_password_hash(hashed_password, plain_password)

