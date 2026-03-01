"""Yandex translator API"""

__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

import os

from deep_translator.base import BaseTranslator
from deep_translator.constants import BASE_URLS, DEFAULT_TIMEOUT, YANDEX_ENV_VAR
from deep_translator.exceptions import (
    ApiKeyException,
    RequestError,
    ServerException,
    TooManyRequests,
    TranslationNotFound,
)
from deep_translator.validate import is_input_valid, request_failed


class YandexTranslator(BaseTranslator):
    """
    class that wraps functions, which use the yandex translator
    under the hood to translate word(s)
    """

    def __init__(
        self,
        source: str = "en",
        target: str = "de",
        api_key: str | None = None,
        **kwargs,
    ):
        """
        @param api_key: your yandex api key
        """
        if api_key is None:
            api_key = os.getenv(YANDEX_ENV_VAR)

        if not api_key:
            raise ApiKeyException(YANDEX_ENV_VAR)
        self.api_key = api_key
        self.api_version = "v1.5"
        self.api_endpoints = {
            "langs": "getLangs",
            "detect": "detect",
            "translate": "translate",
        }
        super().__init__(
            base_url=BASE_URLS.get("YANDEX"),
            source=source,
            target=target,
            **kwargs,
        )

    def _get_supported_languages(self):
        return set(x.split("-")[0] for x in self.dirs)

    @property
    def languages(self):
        return self.get_supported_languages()

    @property
    def dirs(self, proxies: dict | None = None):
        try:
            url = self._base_url.format(
                version=self.api_version, endpoint="getLangs"
            )
            session = self._get_session()
            response = session.get(
                url,
                params={"key": self.api_key},
                proxies=proxies,
                timeout=DEFAULT_TIMEOUT,
            )
        except ConnectionError:
            raise ServerException(503)
        else:
            data = response.json()

        if request_failed(status_code=response.status_code):
            raise ServerException(response.status_code)
        return data.get("dirs")

    def detect(self, text: str, proxies: dict | None = None):
        response = None
        params = {
            "text": text,
            "format": "plain",
            "key": self.api_key,
        }
        try:
            url = self._base_url.format(
                version=self.api_version, endpoint="detect"
            )
            session = self._get_session()
            response = session.post(
                url, data=params, proxies=proxies, timeout=DEFAULT_TIMEOUT
            )
        except RequestError:
            raise
        except ConnectionError:
            raise ServerException(503)
        except ValueError:
            raise ServerException(response.status_code)
        else:
            response = response.json()
        language = response["lang"]
        status_code = response["code"]
        if status_code != 200:
            raise RequestError()
        elif not language:
            raise ServerException(501)
        return language

    def translate(
        self, text: str, proxies: dict | None = None, **kwargs
    ) -> str:
        if is_input_valid(text):
            params = {
                "text": text,
                "format": "plain",
                "lang": self._target
                if self._source == "auto"
                else f"{self._source}-{self._target}",
                "key": self.api_key,
            }
            try:
                url = self._base_url.format(
                    version=self.api_version, endpoint="translate"
                )
                session = self._get_session()
                response = session.post(
                    url, data=params, proxies=proxies, timeout=DEFAULT_TIMEOUT
                )
            except ConnectionError:
                raise ServerException(503)
            else:
                response = response.json()

            if response["code"] == 429:
                raise TooManyRequests()

            if response["code"] != 200:
                raise ServerException(response["code"])

            if not response["text"]:
                raise TranslationNotFound()

            return response["text"]
