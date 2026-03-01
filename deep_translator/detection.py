"""Language detection API"""

__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

import logging

import requests
from requests.exceptions import HTTPError

from deep_translator.constants import DEFAULT_TIMEOUT
from deep_translator.exceptions import ApiKeyException, NotValidPayload

logger = logging.getLogger(__name__)

_DETECT_URL = "https://ws.detectlanguage.com/0.2/detect"
_USER_AGENT = "Detect Language API Python Client 1.4.0"


def get_request_body(
    text: str | list[str], api_key: str, *args, **kwargs
):
    """
    send a request and return the response body parsed as dictionary

    @param text: target text that you want to detect its language
    @type text: str
    @type api_key: str
    @param api_key: your private API key
    """
    if not api_key:
        raise ApiKeyException(
            env_var="DETECTLANGUAGE_API_KEY",
        )
    if not text:
        raise NotValidPayload(text)

    try:
        headers = {
            "User-Agent": _USER_AGENT,
            "Authorization": f"Bearer {api_key}",
        }
        response = requests.post(
            _DETECT_URL,
            json={"q": text},
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        )
        body = response.json().get("data")
        return body

    except HTTPError as e:
        logger.error("Error occurred while requesting from server: %s", e)
        raise


def single_detection(
    text: str,
    api_key: str | None = None,
    detailed: bool = False,
    *args,
    **kwargs,
):
    """
    function responsible for detecting the language from a text

    @param text: target text that you want to detect its language
    @type text: str
    @type api_key: str
    @param api_key: your private API key
    @param detailed: set to True if you want to get detailed
    information about the detection process
    """
    body = get_request_body(text, api_key)
    detections = body.get("detections")
    if detailed:
        return detections[0]

    lang = detections[0].get("language", None)
    if lang:
        return lang


def batch_detection(
    text_list: list[str],
    api_key: str,
    detailed: bool = False,
    *args,
    **kwargs,
):
    """
    function responsible for detecting the language from a text

    @param text_list: target batch that you want to detect its language
    @param api_key: your private API key
    @param detailed: set to True if you want to
    get detailed information about the detection process
    """
    body = get_request_body(text_list, api_key)
    detections = body.get("detections")
    res = [obj[0] for obj in detections]
    if detailed:
        return res
    return [obj["language"] for obj in res]
