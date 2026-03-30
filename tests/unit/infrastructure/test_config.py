import pytest

from documentor.infrastructure.config import Settings


def test_settings_should_have_default_search_language_english() -> None:
    settings = Settings(database_url="postgresql+asyncpg://x:x@localhost/x")
    assert settings.search_language == "english"


def test_settings_should_have_default_rrf_k_sixty() -> None:
    settings = Settings(database_url="postgresql+asyncpg://x:x@localhost/x")
    assert settings.rrf_k == 60


def test_settings_should_read_search_language_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEARCH_LANGUAGE", "spanish")
    settings = Settings(database_url="postgresql+asyncpg://x:x@localhost/x")
    assert settings.search_language == "spanish"


def test_settings_should_read_rrf_k_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RRF_K", "30")
    settings = Settings(database_url="postgresql+asyncpg://x:x@localhost/x")
    assert settings.rrf_k == 30
