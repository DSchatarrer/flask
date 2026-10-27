"""Checks sin Flask para detectar regresiones estructurales."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_project_is_organized_by_domain():
    assert (ROOT / "src/applications/login/router.py").is_file()
    assert (ROOT / "src/applications/login/controller.py").is_file()
    assert (ROOT / "src/applications/login/schemas.py").is_file()
    assert (ROOT / "src/applications/users/router.py").is_file()
    assert (ROOT / "src/core/manager_db.py").is_file()
    assert (ROOT / "src/core/models/base.py").is_file()


def test_no_sqlmodel_or_vendor_specific_model_dialects():
    for path in (ROOT / "src").rglob("*.py"):
        content = path.read_text()
        assert "sqlmodel" not in content.lower(), path
        assert "sqlalchemy.dialects.postgresql" not in content, path


def test_guards_never_cleanup_or_commit():
    sec = (ROOT / "src/core/security.py").read_text()
    assert "purge_expired_sessions" not in sec
    assert "cleanup_expired_sessions(" not in sec
    assert "db.commit(" not in sec
    assert "db.execute(delete(" not in sec


def test_login_controller_does_not_manage_http_responses():
    controller = (ROOT / "src/applications/login/controller.py").read_text()
    assert "from flask import" not in controller
    assert "from flask_smorest" not in controller
    assert "set_cookie(" not in controller


def test_factory_created_only_at_app_level():
    dbfile = (ROOT / "src/core/manager_db.py").read_text()
    assert 'app.extensions["session_factory"] = factory' in dbfile
    assert 'with get_session() as db:' in dbfile
