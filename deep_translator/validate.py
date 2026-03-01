__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

from deep_translator.exceptions import NotValidLength, NotValidPayload


def is_empty(text: str) -> bool:
    return text == ""


def request_failed(status_code: int) -> bool:
    """Check if a request has failed or not.
    A request is considered successful if the status code is in the 2xx range.

    Args:
        status_code: status code of the request

    Returns:
        True if the request failed, False otherwise.
    """
    return not (200 <= status_code <= 299)


def is_input_valid(
    text: str, min_chars: int = 0, max_chars: int | None = None
) -> bool:
    """
    validate the target text to translate
    @param min_chars: min characters
    @param max_chars: max characters
    @param text: text to translate
    @return: bool
    """

    if not isinstance(text, str):
        raise NotValidPayload(text)
    if max_chars and (not min_chars <= len(text) < max_chars):
        raise NotValidLength(text, min_chars, max_chars)

    return True
