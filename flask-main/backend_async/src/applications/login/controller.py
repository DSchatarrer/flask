"""Casos de uso async, independientes del protocolo HTTP."""
import asyncio

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.security import check_password_hash, generate_password_hash

from src.core.models.sessions import Sessions
from src.core.models.users import Users
from src.core.security import create_token, get_uuid_and_exp_from_token


class InvalidCredentials(Exception):
    """Error uniforme sin revelar usuarios existentes."""


class UserAlreadyExists(Exception):
    """Usuario duplicado."""


class LoginController:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(self, username: str, password: str) -> str:
        user = await self.db.get(Users, username)
        if not user or not user.hash_pwd or not await asyncio.to_thread(check_password_hash, user.hash_pwd, password):
            raise InvalidCredentials
        token = create_token()
        session_id, expiration = get_uuid_and_exp_from_token(token)
        self.db.add(Sessions(token=session_id, usu=username, exp=expiration))
        await self.db.commit()
        return token

    async def create_user(self, username: str, password: str, role: str) -> None:
        if await self.db.get(Users, username):
            raise UserAlreadyExists
        password_hash = await asyncio.to_thread(generate_password_hash, password)
        self.db.add(Users(usu=username, hash_pwd=password_hash, role=role))
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise UserAlreadyExists from exc
