from nova.core.secret_store import (
    get_secret,
    require_secret,
    secret_env_name,
)


def test_secret_env_name_uses_nova_prefix():
    assert secret_env_name("gemini_api_key") == "NOVA_GEMINI_API_KEY"
    assert secret_env_name("groq-api-key") == "NOVA_GROQ_API_KEY"


def test_get_secret_reads_prefixed_variable():
    environ = {"NOVA_GEMINI_API_KEY": "abc123"}

    assert get_secret("gemini_api_key", environ) == "abc123"


def test_missing_or_blank_secret_is_none():
    assert get_secret("gemini_api_key", {}) is None
    assert get_secret("gemini_api_key", {"NOVA_GEMINI_API_KEY": "  "}) is None


def test_require_secret_fails_with_structured_error():
    result = require_secret("gemini_api_key", {})

    assert not result.success
    assert result.error.code == "SECRET_NOT_FOUND"
    assert "NOVA_GEMINI_API_KEY" in result.error.message


def test_require_secret_reads_real_environment(monkeypatch):
    monkeypatch.setenv("NOVA_TEST_SECRET", "valor-secreto")

    result = require_secret("test_secret")

    assert result.success
    assert result.value == "valor-secreto"