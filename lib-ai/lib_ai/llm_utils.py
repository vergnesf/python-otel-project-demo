"""
LLM utilities for safe response handling
"""


def extract_text_from_response(response: object) -> str:
    """
    Safely extract text from LLM response objects.

    Handles different response types from various LLM providers,
    including LangChain objects and legacy API responses.

    Args:
        response: LLM response object (any type)

    Returns:
        Extracted text content as string
    """
    # Try content attribute (most common)
    try:
        if hasattr(response, "content"):
            content = response.content
            if content is not None:
                return str(content)
    except (AttributeError, Exception):
        pass

    # Try text attribute (alternative)
    try:
        if hasattr(response, "text"):
            text = response.text
            if text is not None:
                return str(text)
    except (AttributeError, Exception):
        pass

    # Fallback to string representation
    try:
        return str(response)
    except Exception:
        return ""
