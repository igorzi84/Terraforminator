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


def test_unset_host_variable(monkeypatch):
    monkeypatch.delenv("TERRAFORMINATOR_HOST", raising=False)

    settings = load_app_settings()
    assert settings.host == "127.0.0.1"


def test_whitespace_host(monkeypatch):
    monkeypatch.setenv("TERRAFORMINATOR_HOST", " 0.0.0.0 ")

    settings = load_app_settings()
    assert settings.host == "0.0.0.0"


@pytest.mark.parametrize("host", ["", " "])
def test_empty_unset_host(monkeypatch, host):
    monkeypatch.setenv("TERRAFORMINATOR_HOST", host)

    with pytest.raises(ValueError):
        load_app_settings()


def test_unset_temporal_address(monkeypatch):
    monkeypatch.delenv("TERRAFORMINATOR_TEMPORAL_ADDRESS", raising=False)

    assert load_app_settings().temporal_address == "localhost:7233"


def test_whitespace_temporal_address(monkeypatch):
    monkeypatch.setenv("TERRAFORMINATOR_TEMPORAL_ADDRESS", " temporal.test:7233 ")

    assert load_app_settings().temporal_address == "temporal.test:7233"


@pytest.mark.parametrize("address", ["", " "])
def test_empty_temporal_address(monkeypatch, address):
    monkeypatch.setenv("TERRAFORMINATOR_TEMPORAL_ADDRESS", address)

    with pytest.raises(ValueError, match="TERRAFORMINATOR_TEMPORAL_ADDRESS"):
        load_app_settings()
