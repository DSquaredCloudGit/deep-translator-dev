"""LibreTranslate API"""

__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

import os

from deep_translator.base import BaseTranslator
from deep_translator.constants import (
    BASE_URLS,
    DEFAULT_TIMEOUT,
    LIBRE_ENV_VAR,
    LIBRE_LANGUAGES_TO_CODES,
)
from deep_translator.exceptions import (
    ApiKeyException,
    AuthorizationException,
    ServerException,
    TranslationNotFound,
)
from deep_translator.validate import is_empty, is_input_valid, request_failed


class LibreTranslator(BaseTranslator):
    """
    class that wraps functions, which use libre translator under the hood to translate text(s)
    """

    def __init__(
        self,
        source: str = "en",
        target: str = "es",
        api_key: str | None = None,
        use_free_api: bool = True,
        custom_url: str | None = None,
        **kwargs,
    ):
        """
        @param api_key: your api key
        @param source: source language to translate from
        @param target: target language to translate to
        @param use_free_api: set True if you want to use the free api
        @param custom_url: you can use a custom endpoint
        """
        if api_key is None:
            api_key = os.getenv(LIBRE_ENV_VAR)

        if not api_key:
            raise ApiKeyException(env_var=LIBRE_ENV_VAR)

        self.api_key = api_key
        url = (
            BASE_URLS.get("LIBRE")
            if not use_free_api
            else BASE_URLS.get("LIBRE_FREE")
        )
        super().__init__(
            base_url=url if not custom_url else custom_url,
            source=source,
            target=target,
            languages=LIBRE_LANGUAGES_TO_CODES,
        )

    def translate(self, text: str, **kwargs) -> str:
        """
        Translate a text using LibreTranslate.

        @param text: desired text to translate
        @return: str: translated text
        """
        if is_input_valid(text):
            if self._same_source_target() or is_empty(text):
                return text

            translate_endpoint = "translate"
            params = {
                "q": text,
                "source": self._source,
                "target": self._target,
                "format": "text",
            }
            if self.api_key:
                params["api_key"] = self.api_key
            try:
                session = self._get_session()
                response = session.post(
                    self._base_url + translate_endpoint,
                    params=params,
                    timeout=DEFAULT_TIMEOUT,
                )
            except ConnectionError:
                raise ServerException(503)

            if response.status_code == 403:
                raise AuthorizationException(self.api_key)
            elif request_failed(status_code=response.status_code):
                raise ServerException(response.status_code)
            res = response.json()
            if not res:
                raise TranslationNotFound(text)
            return res["translatedText"]
