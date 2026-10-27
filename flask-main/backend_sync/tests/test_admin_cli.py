from sqlalchemy import select
from src.core.models.users import Users


def test_create_admin_cli_for_bootstrap(app):
    runner = app.test_cli_runner()
    res = runner.invoke(args=["create-admin", "--username", "superadmin"], input="strongpassword\nstrongpassword\n")
    assert res.exit_code == 0, res.output
    with app.app_context():
        with app.extensions["session_factory"]() as db:
            user = db.get(Users, "superadmin")
            assert user is not None and user.role == "admin"


def test_create_admin_rejects_duplicates(app):
    runner = app.test_cli_runner()
    res = runner.invoke(args=["create-admin", "--username", "admin"], input="otherpassword\notherpassword\n")
    assert res.exit_code != 0
