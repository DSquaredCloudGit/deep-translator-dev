# -*- coding: utf-8 -*-

__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

import logging
import os

from deep_translator.base import BaseTranslator
from deep_translator.constants import BASE_URLS, DEFAULT_TIMEOUT, MSFT_ENV_VAR
from deep_translator.exceptions import (
    ApiKeyException,
    MicrosoftAPIerror,
    TranslationNotFound,
)
from deep_translator.validate import is_input_valid

logger = logging.getLogger(__name__)

# Class-level cache so we only fetch languages once
_msft_languages_cache: dict | None = None


class MicrosoftTranslator(BaseTranslator):
    """
    class that wraps functions, which use the Microsoft translator under the hood to translate word(s)
    """

    def __init__(
        self,
        source: str = "auto",
        target: str = "en",
        api_key: str | None = None,
        region: str | None = None,
        proxies: dict | None = None,
        **kwargs,
    ):
        """
        @param api_key: your Microsoft API key
        @param region: your Microsoft Location
        """
        if api_key is None:
            api_key = os.getenv(MSFT_ENV_VAR)

        if not api_key:
            raise ApiKeyException(env_var=MSFT_ENV_VAR)

        self.api_key = api_key
        self.proxies = proxies
        self.headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-type": "application/json",
        }
        if region:
            self.region = region
            self.headers["Ocp-Apim-Subscription-Region"] = self.region
        super().__init__(
            base_url=BASE_URLS.get("MICROSOFT_TRANSLATE"),
            source=source,
            target=target,
            languages=self._get_supported_languages(),
            **kwargs,
        )

    def _get_supported_languages(self) -> dict:
        global _msft_languages_cache
        if _msft_languages_cache is not None:
            return _msft_languages_cache

        microsoft_languages_api_url = (
            "https://api.cognitive.microsofttranslator.com/languages"
            "?api-version=3.0&scope=translation"
        )
        session = self._get_session()
        resp = session.get(microsoft_languages_api_url, timeout=DEFAULT_TIMEOUT)
        translation_dict = resp.json()["translation"]
        _msft_languages_cache = {
            translation_dict[k]["name"].lower(): k.lower()
            for k in translation_dict
        }
        return _msft_languages_cache

    def translate(self, text: str, **kwargs) -> str:
        """
        function that uses microsoft translate to translate a text
        @param text: desired text to translate
        @return: str: translated text
        """
        response = None
        if is_input_valid(text):
            self._url_params["from"] = self._source
            self._url_params["to"] = self._target

            valid_microsoft_json = [{"text": text}]
            try:
                session = self._get_session()
                response = session.post(
                    self._base_url,
                    params=self._url_params,
                    headers=self.headers,
                    json=valid_microsoft_json,
                    proxies=self.proxies,
                    timeout=DEFAULT_TIMEOUT,
                )
            except Exception as exc:
                logger.warning("Returned error: %s", type(exc).__name__)

            if response is None:
                raise TranslationNotFound(text)

            # Microsoft API returns a dict on error, a list on success
            data = response.json()
            if isinstance(data, dict):
                error_message = data["error"]
                raise MicrosoftAPIerror(error_message)
            elif isinstance(data, list):
                all_translations = [
                    i["text"] for i in data[0]["translations"]
                ]
                return "\n".join(all_translations)
