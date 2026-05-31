import pytest

from app.config import load_settings


def test_load_settings_raises_when_missing_required_env(monkeypatch):
    # Use empty values so .env loader does not refill them during the test.
    monkeypatch.setenv("META_APP_ID", "")
    monkeypatch.setenv("META_APP_SECRET", "")
    monkeypatch.setenv("INSTAGRAM_ACCOUNT_ID", "")
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "")
    monkeypatch.setenv("REDIRECT_URI", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")

    with pytest.raises(ValueError) as exc:
        load_settings()

    message = str(exc.value)
    assert "META_APP_ID" in message
    assert "META_APP_SECRET" in message
    assert "ANTHROPIC_API_KEY" in message
