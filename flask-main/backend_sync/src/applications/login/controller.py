"""Casos de uso independientes de Flask/HTTP: login y alta de usuarios."""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from src.core.models.sessions import Sessions
from src.core.models.users import Users
from src.core.security import create_token, get_uuid_and_exp_from_token


class InvalidCredentials(Exception):
    """Credenciales incorrectas sin revelar existencia de usuarios."""


class UserAlreadyExists(Exception):
    """Conflicto de nombre de usuario."""


class LoginController:
    def __init__(self, db: Session):
        self.db = db

    def login(self, username: str, password: str) -> str:
        user = self.db.get(Users, username)
        if not user or not user.hash_pwd or not check_password_hash(user.hash_pwd, password):
            raise InvalidCredentials
        token = create_token()
        session_id, expiration = get_uuid_and_exp_from_token(token)
        self.db.add(Sessions(token=session_id, usu=username, exp=expiration))
        self.db.commit()
        return token

    def create_user(self, username: str, password: str, role: str) -> None:
        if self.db.get(Users, username):
            raise UserAlreadyExists
        self.db.add(Users(usu=username, hash_pwd=generate_password_hash(password), role=role))
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise UserAlreadyExists from exc
