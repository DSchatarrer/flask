from src.core.models.users import Users
from tests.conftest import run_async


def test_create_admin_cli_for_bootstrap(app):
    runner = app.test_cli_runner()
    res = runner.invoke(args=["create-admin", "--username", "superadmin"], input="strongpassword\nstrongpassword\n")
    assert res.exit_code == 0, res.output
    async def verify():
        factory = app.extensions["session_factory"]
        async with factory() as db:
            user = await db.get(Users, "superadmin")
            assert user is not None and user.role == "admin"
    with app.app_context():
        run_async(verify())


def test_create_admin_rejects_duplicates(app):
    runner = app.test_cli_runner()
    res = runner.invoke(args=["create-admin", "--username", "admin"], input="otherpassword\notherpassword\n")
    assert res.exit_code != 0
