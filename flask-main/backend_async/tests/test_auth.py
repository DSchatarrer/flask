from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

from src.core.models.sessions import Sessions
from src.core.models.users import Users
from tests.conftest import login, run_async


def test_public_routes(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").json == {"status": "ok"}


def test_openapi_documentation(client):
    assert client.get("/docs").status_code == 200


def test_login_invalid_credentials_are_uniform(client):
    assert client.post("/login/", json={"user": "missing", "password": "whatever"}).status_code == 401
    assert client.post("/login/", json={"user": "admin", "password": "bad"}).status_code == 401


def test_login_and_restricted_endpoint(client):
    assert client.get("/users/users", headers={"X-API-Key": "test-api-key"}).status_code == 401
    response = login(client)
    assert response.status_code == 200
    assert "X-Sync.Ref=" in response.headers["Set-Cookie"]
    assert "HttpOnly" in response.headers["Set-Cookie"]
    assert client.get("/users/users").status_code == 401
    result = client.get("/users/users", headers={"X-API-Key": "test-api-key"})
    assert result.status_code == 200
    assert result.json == {"hola": "admin"}
    assert "eyJ" not in str(result.json)


def test_registration_requires_admin(client, app):
    payload = {"user": "newuser", "password": "password123", "role": "admin"}
    assert client.post("/login/register", json=payload).status_code == 401
    assert login(client, "worker", "workerpass").status_code == 200
    assert client.post("/login/register", json=payload).status_code == 403
    assert login(client).status_code == 200
    assert client.post("/login/register", json=payload).status_code == 201
    assert client.post("/login/register", json=payload).status_code == 409
    async def verify():
        async with app.extensions["session_factory"]() as db:
            assert (await db.get(Users, "newuser")).role == "admin"
    with app.app_context():
        run_async(verify())


def test_expired_db_session_denied_without_deletion(client, app):
    assert login(client).status_code == 200
    async def expire_and_verify(check_only=False):
        factory = app.extensions["session_factory"]
        if not check_only:
            async with factory.begin() as db:
                await db.execute(update(Sessions).values(exp=datetime.now(timezone.utc) - timedelta(days=10)))
        else:
            async with factory() as db:
                return len((await db.scalars(select(Sessions))).all())
    with app.app_context():
        run_async(expire_and_verify())
    assert client.get("/users/users", headers={"X-API-Key": "test-api-key"}).status_code == 401
    with app.app_context():
        assert run_async(expire_and_verify(check_only=True)) == 1


def test_cleanup_is_separate_cli_command(client, app):
    assert login(client).status_code == 200
    async def expire_and_query(query=False):
        factory = app.extensions["session_factory"]
        if not query:
            async with factory.begin() as db:
                await db.execute(update(Sessions).values(exp=datetime.now(timezone.utc) - timedelta(days=10)))
        else:
            async with factory() as db:
                return (await db.scalars(select(Sessions))).all()
    with app.app_context():
        run_async(expire_and_query())
    result = app.test_cli_runner().invoke(args=["cleanup-sessions", "--retention-days", "7"])
    assert result.exit_code == 0, result.output
    with app.app_context():
        assert run_async(expire_and_query(query=True)) == []


def test_cookie_api_key_legacy_query_supported(client):
    assert login(client).status_code == 200
    assert client.get("/users/users?apikey=test-api-key").status_code == 200
