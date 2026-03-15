"""Unit tests for lib_ai.llm_config — model params loading and LLM factory.

Coverage:
- load_model_params_config(): fallback to hardcoded defaults when no YAML file found
- get_model_params(): exact match, base-name match, fallback to default
- get_llm(): correct params forwarded (model, temperature, max_tokens)
"""

from unittest.mock import MagicMock, patch

import lib_ai.llm_config as llm_config_module
import pytest
from lib_ai.llm_config import get_llm, get_model_params, load_model_params_config


@pytest.fixture(autouse=True)
def reset_config_cache():
    """Reset the module-level config cache between tests."""
    llm_config_module._MODEL_PARAMS_CONFIG = None
    yield
    llm_config_module._MODEL_PARAMS_CONFIG = None


# ---------------------------------------------------------------------------
# load_model_params_config
# ---------------------------------------------------------------------------


def test_load_model_params_config_fallback_when_no_file():
    """When no YAML file exists at any known path, fallback defaults are returned."""
    from pathlib import Path

    llm_config_module._MODEL_PARAMS_CONFIG = None
    with patch.object(Path, "exists", return_value=False):
        config = load_model_params_config()

    assert "default" in config
    assert config["default"]["temperature"] == 0.1
    assert config["default"]["max_tokens"] == 2000
    assert "models" in config


def test_load_model_params_config_cached():
    """Second call returns cached result without re-reading files."""
    sentinel = {"default": {"temperature": 0.99}, "models": {}}
    llm_config_module._MODEL_PARAMS_CONFIG = sentinel
    result = load_model_params_config()
    assert result is sentinel


# ---------------------------------------------------------------------------
# get_model_params
# ---------------------------------------------------------------------------

_FAKE_CONFIG = {
    "default": {"temperature": 0.1, "top_k": None, "max_tokens": 2000},
    "models": {
        "qwen3:0.6b": {"temperature": 0.0, "top_k": 20, "max_tokens": 1000},
        "mistral:7b": {"temperature": 0.2, "top_k": None, "max_tokens": 4000},
    },
}


def test_get_model_params_exact_match():
    llm_config_module._MODEL_PARAMS_CONFIG = _FAKE_CONFIG
    params = get_model_params("qwen3:0.6b")
    assert params["temperature"] == 0.0
    assert params["top_k"] == 20
    assert params["max_tokens"] == 1000


def test_get_model_params_base_name_match():
    """'qwen3:1.5b' should match 'qwen3:0.6b' key via base-name prefix."""
    llm_config_module._MODEL_PARAMS_CONFIG = _FAKE_CONFIG
    params = get_model_params("qwen3:1.5b")
    assert params["temperature"] == 0.0


def test_get_model_params_fallback_to_default():
    llm_config_module._MODEL_PARAMS_CONFIG = _FAKE_CONFIG
    params = get_model_params("unknown-model")
    assert params["temperature"] == 0.1
    assert params["max_tokens"] == 2000


# ---------------------------------------------------------------------------
# get_llm
# ---------------------------------------------------------------------------


def test_get_llm_forwards_model_and_params():
    """get_llm() must instantiate SafeChatOpenAI with correct model/params."""
    llm_config_module._MODEL_PARAMS_CONFIG = _FAKE_CONFIG

    with patch("lib_ai.llm_config.SafeChatOpenAI") as mock_cls:
        mock_cls.return_value = MagicMock()
        get_llm(model="qwen3:0.6b")

    mock_cls.assert_called_once()
    call_kwargs = mock_cls.call_args.kwargs
    assert call_kwargs["model"] == "qwen3:0.6b"
    assert call_kwargs["temperature"] == 0.0
    assert call_kwargs["max_tokens"] == 1000


def test_get_llm_explicit_params_override_config():
    """Explicit temperature/max_tokens args take priority over config values."""
    llm_config_module._MODEL_PARAMS_CONFIG = _FAKE_CONFIG

    with patch("lib_ai.llm_config.SafeChatOpenAI") as mock_cls:
        mock_cls.return_value = MagicMock()
        get_llm(model="qwen3:0.6b", temperature=0.9, max_tokens=500)

    call_kwargs = mock_cls.call_args.kwargs
    assert call_kwargs["temperature"] == 0.9
    assert call_kwargs["max_tokens"] == 500


def test_get_llm_uses_env_model(monkeypatch):
    """When model arg is None, LLM_MODEL env var is used."""
    llm_config_module._MODEL_PARAMS_CONFIG = _FAKE_CONFIG
    monkeypatch.setenv("LLM_MODEL", "mistral:7b")

    with patch("lib_ai.llm_config.SafeChatOpenAI") as mock_cls:
        mock_cls.return_value = MagicMock()
        get_llm()

    call_kwargs = mock_cls.call_args.kwargs
    assert call_kwargs["model"] == "mistral:7b"
