from pathlib import Path

import pytest

from terraforminator.config import load_app_settings

ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / "terraforminator.db"


def test_db_path_variable_unset(monkeypatch):
    monkeypatch.delenv("TERRAFORMINATOR_DB_PATH", raising=False)

    settings = load_app_settings()
    assert settings.database_path == DB_PATH


def test_db_path_variable_set(monkeypatch):
    monkeypatch.setenv("TERRAFORMINATOR_DB_PATH", "mydb.db")

    settings = load_app_settings()
    assert settings.database_path == Path("mydb.db")


@pytest.mark.parametrize("path", ["", " "])
def test_empty_path_variable(monkeypatch, path):
    monkeypatch.setenv("TERRAFORMINATOR_DB_PATH", path)

    with pytest.raises(ValueError):
        load_app_settings()
