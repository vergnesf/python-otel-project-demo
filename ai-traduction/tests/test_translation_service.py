"""Unit tests for the translation service."""

from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add project root to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_traduction.translation_service import TranslationService


def _mock_llm_with_side_effect(values: list[str]) -> Mock:
    mock_llm = Mock()
    mock_llm.invoke.side_effect = [Mock(content=value) for value in values]
    return mock_llm


def test_translate_english_query_returns_same_text():
    with patch("ai_traduction.translation_service.get_llm") as mock_get_llm:
        mock_get_llm.return_value = _mock_llm_with_side_effect(["ENGLISH"])

        service = TranslationService()
        result = service.translate("Show me recent errors")

        assert result["language"] == "english"
        assert result["translated_query"] == "Show me recent errors"


def test_translate_non_english_query_translates():
    with patch("ai_traduction.translation_service.get_llm") as mock_get_llm:
        mock_get_llm.return_value = _mock_llm_with_side_effect(
            ["NOT_ENGLISH", "Show me recent errors"]
        )

        service = TranslationService()
        result = service.translate("Montre-moi les erreurs récentes")

        assert result["language"] == "non-english"
        assert result["translated_query"] == "Show me recent errors"


def test_translate_without_llm_falls_back_safely():
    with patch("ai_traduction.translation_service.get_llm") as mock_get_llm:
        mock_get_llm.side_effect = Exception("LLM not available")

        service = TranslationService()
        with patch.object(service, "_ollama_generate", return_value=None):
            result = service.translate("Bonjour")

        assert result["language"] == "unknown"
        assert result["translated_query"] == "Bonjour"


def test_translate_empty_query_returns_unknown():
    service = TranslationService()

    result = service.translate("")

    assert result["language"] == "unknown"
    assert result["translated_query"] == ""
