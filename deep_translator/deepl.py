__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

import os

from deep_translator.base import BaseTranslator
from deep_translator.constants import (
    BASE_URLS,
    DEFAULT_TIMEOUT,
    DEEPL_ENV_VAR,
    DEEPL_LANGUAGE_TO_CODE,
)
from deep_translator.exceptions import (
    ApiKeyException,
    AuthorizationException,
    ServerException,
    TranslationNotFound,
)
from deep_translator.validate import is_empty, is_input_valid, request_failed


class DeeplTranslator(BaseTranslator):
    """
    class that wraps functions, which use the DeeplTranslator translator
    under the hood to translate word(s)
    """

    def __init__(
        self,
        source: str = "de",
        target: str = "en",
        api_key: str | None = None,
        use_free_api: bool = True,
        **kwargs,
    ):
        """
        @param api_key: your DeeplTranslator api key.
        Get one here: https://www.deepl.com/docs-api/accessing-the-api/
        @param source: source language
        @param target: target language
        """
        if api_key is None:
            api_key = os.getenv(DEEPL_ENV_VAR)

        if not api_key:
            raise ApiKeyException(env_var=DEEPL_ENV_VAR)

        self.version = "v2"
        self.api_key = api_key
        url = (
            BASE_URLS.get("DEEPL_FREE").format(version=self.version)
            if use_free_api
            else BASE_URLS.get("DEEPL").format(version=self.version)
        )
        super().__init__(
            base_url=url,
            source=source,
            target=target,
            languages=DEEPL_LANGUAGE_TO_CODE,
            **kwargs,
        )

    def translate(self, text: str, **kwargs) -> str:
        """
        @param text: text to translate
        @return: translated text
        """
        if is_input_valid(text):
            if self._same_source_target() or is_empty(text):
                return text

            translate_endpoint = "translate"
            params = {
                "auth_key": self.api_key,
                "source_lang": self._source,
                "target_lang": self._target,
                "text": text,
            }
            try:
                session = self._get_session()
                response = session.get(
                    self._base_url + translate_endpoint,
                    params=params,
                    timeout=DEFAULT_TIMEOUT,
                )
            except ConnectionError:
                raise ServerException(503)
            if response.status_code == 403:
                raise AuthorizationException(self.api_key)
            if request_failed(status_code=response.status_code):
                raise ServerException(response.status_code)
            res = response.json()
            if not res:
                raise TranslationNotFound(text)
            return res["translations"][0]["text"]
