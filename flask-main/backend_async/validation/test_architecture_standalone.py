"""Análisis estructural sin depender de Flask ni de drivers externos."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_domain_structure():
    for name in (
        "src/main.py", "src/asgi.py", "src/core/manager_db.py",
        "src/applications/login/router.py", "src/applications/login/controller.py",
        "src/applications/login/schemas.py", "src/applications/users/router.py",
        "src/core/models/base.py", "migrations/env.py",
    ):
        assert (ROOT / name).is_file(), name


def test_all_python_files_compile():
    for f in ROOT.rglob("*.py"):
        compile(f.read_text(encoding="utf-8"), str(f), "exec")


def test_async_routes_controllers_db():
    paths_and_names = {
        "src/core/manager_db.py": {"get_session", "init_db", "dispose_database"},
        "src/core/security.py": set(),
        "src/core/session_cleanup.py": {"cleanup_expired_sessions"},
        "src/applications/login/controller.py": {"login", "create_user"},
        "src/applications/login/router.py": {"post"},
        "src/applications/users/router.py": {"get"},
        "src/applications/home/router.py": {"get"},
    }
    for filename, names in paths_and_names.items():
        tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
        async_functions = {x.name for x in ast.walk(tree) if isinstance(x, ast.AsyncFunctionDef)}
        assert names <= async_functions, (filename, names - async_functions)
    db_source = (ROOT / "src/core/manager_db.py").read_text()
    assert "async_sessionmaker" in db_source and "create_async_engine" in db_source
    assert "NullPool" in db_source
    assert 'app.extensions["session_factory"] = factory' in db_source
    assert "async with get_session() as db" in db_source


def test_guards_are_read_only():
    sec = (ROOT / "src/core/security.py").read_text()
    assert "cleanup_expired_sessions(" not in sec
    assert "db.commit(" not in sec
    assert "db.execute(delete(" not in sec
    assert "await db.get(" in sec


def test_controller_does_not_depend_on_http():
    controller = (ROOT / "src/applications/login/controller.py").read_text()
    assert "from flask import" not in controller
    assert "from flask_smorest" not in controller
    assert "set_cookie(" not in controller


def test_model_schema_remains_generic():
    for f in (ROOT / "src/core/models").rglob("*.py"):
        source = f.read_text()
        assert "sqlmodel" not in source.lower()
        assert "sqlalchemy.dialects.postgresql" not in source
