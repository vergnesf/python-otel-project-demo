"""Unit tests for lib_ai.llm_utils — LLM response text extraction utilities."""

from lib_ai.llm_utils import extract_text_from_response


class _WithContent:
    content = "hello from content"


class _WithText:
    text = "hello from text"


class _WithNoneContent:
    content = None


class _WithNoneText:
    text = None


class _WithBothContentAndText:
    content = "content wins"
    text = "text loses"


def test_extract_content_attribute():
    assert extract_text_from_response(_WithContent()) == "hello from content"


def test_extract_text_attribute_fallback():
    assert extract_text_from_response(_WithText()) == "hello from text"


def test_content_takes_priority_over_text():
    assert extract_text_from_response(_WithBothContentAndText()) == "content wins"


def test_none_content_falls_through_to_text():
    obj = _WithNoneContent()
    obj.text = "fallback text"
    assert extract_text_from_response(obj) == "fallback text"


def test_fallback_to_str_representation():
    assert extract_text_from_response(42) == "42"
    assert extract_text_from_response(["a", "b"]) == "['a', 'b']"


def test_plain_string_input():
    assert extract_text_from_response("direct string") == "direct string"
