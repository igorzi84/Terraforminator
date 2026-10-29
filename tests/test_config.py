from pathlib import Path

import pytest

from plangate.config import load_app_settings

ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / "plangate.db"


def test_db_path_variable_unset(monkeypatch):
    monkeypatch.delenv("PLANGATE_DB_PATH", raising=False)

    settings = load_app_settings()
    assert settings.db_path == DB_PATH


def test_db_path_variable_set(monkeypatch):
    monkeypatch.setenv("PLANGATE_DB_PATH", "mydb.db")

    settings = load_app_settings()
    assert settings.db_path == Path("mydb.db")


@pytest.mark.parametrize("path", ["", " "])
def test_empty_path_variable(monkeypatch, path):
    monkeypatch.setenv("PLANGATE_DB_PATH", path)

    with pytest.raises(ValueError):
        load_app_settings()


def test_unset_host_variable(monkeypatch):
    monkeypatch.delenv("PLANGATE_HOST", raising=False)

    settings = load_app_settings()
    assert settings.host == "127.0.0.1"


def test_whitespace_host(monkeypatch):
    monkeypatch.setenv("PLANGATE_HOST", " 0.0.0.0 ")

    settings = load_app_settings()
    assert settings.host == "0.0.0.0"


@pytest.mark.parametrize("host", ["", " "])
def test_empty_unset_host(monkeypatch, host):
    monkeypatch.setenv("PLANGATE_HOST", host)

    with pytest.raises(ValueError):
        load_app_settings()


def test_unset_temporal_address(monkeypatch):
    monkeypatch.delenv("PLANGATE_TEMPORAL_ADDRESS", raising=False)

    assert load_app_settings().temporal_address == "localhost:7233"


def test_whitespace_temporal_address(monkeypatch):
    monkeypatch.setenv("PLANGATE_TEMPORAL_ADDRESS", " temporal.test:7233 ")

    assert load_app_settings().temporal_address == "temporal.test:7233"


@pytest.mark.parametrize(
    "address, failure_reason",
    [
        ("", "PLANGATE_TEMPORAL_ADDRESS must be a valid host:port"),
        (" ", "PLANGATE_TEMPORAL_ADDRESS must be a valid host:port"),
        ("host:abc", "Temporal port must be a number"),
        ("host:70000", "Temporal port must be between 1 and 65535"),
    ],
)
def test_invalid_temporal_address(monkeypatch, address, failure_reason):
    monkeypatch.setenv("PLANGATE_TEMPORAL_ADDRESS", address)

    with pytest.raises(ValueError, match=failure_reason):
        load_app_settings()


def test_env_config(monkeypatch):
    monkeypatch.setenv("PLANGATE_LLM_PROVIDER", "test-provider")
    monkeypatch.setenv("PLANGATE_LLM_MODEL", "test-model")
    monkeypatch.setenv("PLANGATE_LLM_TIMEOUT", "15")
    monkeypatch.setenv("PLANGATE_OLLAMA_URL", "http://testurl:12345")
    settings = load_app_settings()

    assert settings.llm_provider == "test-provider"
    assert settings.llm_model == "test-model"
    assert settings.llm_timeout == 15
    assert str(settings.ollama_url) == "http://testurl:12345/"


@pytest.mark.parametrize("timeout", ["0", "-1", "abc"])
def test_invalid_llm_timeout(monkeypatch, timeout):
    monkeypatch.setenv("PLANGATE_LLM_TIMEOUT", timeout)
    with pytest.raises(ValueError):
        load_app_settings()


@pytest.mark.parametrize("url", ["ftp://localhost:11434", "not-a-url"])
def test_invalid_ollama_url(monkeypatch, url):
    monkeypatch.setenv("PLANGATE_OLLAMA_URL", url)
    with pytest.raises(ValueError):
        load_app_settings()