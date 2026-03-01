__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

import os

from deep_translator.base import BaseTranslator
from deep_translator.constants import (
    BASE_URLS,
    DEFAULT_TIMEOUT,
    QCRI_ENV_VAR,
    QCRI_LANGUAGE_TO_CODE,
)
from deep_translator.exceptions import (
    ApiKeyException,
    ServerException,
    TranslationNotFound,
)
from deep_translator.validate import request_failed


class QcriTranslator(BaseTranslator):
    """
    class that wraps functions, which use the QCRI translator
    under the hood to translate word(s)
    """

    def __init__(
        self,
        source: str = "en",
        target: str = "en",
        api_key: str | None = None,
        **kwargs,
    ):
        """
        @param api_key: your QCRI api key.
        Get one for free here https://mt.qcri.org/api/v1/ref
        """
        if api_key is None:
            api_key = os.getenv(QCRI_ENV_VAR)

        if not api_key:
            raise ApiKeyException(QCRI_ENV_VAR)

        self.api_key = api_key
        self.api_endpoints = {
            "get_languages": "getLanguagePairs",
            "get_domains": "getDomains",
            "translate": "translate",
        }

        self.params = {"key": self.api_key}
        super().__init__(
            base_url=BASE_URLS.get("QCRI"),
            source=source,
            target=target,
            languages=QCRI_LANGUAGE_TO_CODE,
            **kwargs,
        )

    def _get(
        self,
        endpoint: str,
        params: dict | None = None,
        return_text: bool = True,
    ):
        if not params:
            params = self.params
        session = self._get_session()
        res = session.get(
            self._base_url.format(endpoint=self.api_endpoints[endpoint]),
            params=params,
            timeout=DEFAULT_TIMEOUT,
        )
        return res.text if return_text else res

    @property
    def languages(self):
        return self.get_supported_languages()

    def get_domains(self):
        return self._get("get_domains")

    @property
    def domains(self):
        return self.get_domains()

    def translate(self, text: str, **kwargs) -> str:
        params = {
            "key": self.api_key,
            "langpair": f"{self._source}-{self._target}",
            "domain": kwargs["domain"],
            "text": text,
        }
        try:
            response = self._get("translate", params=params, return_text=False)
        except ConnectionError:
            raise ServerException(503)
        else:
            if request_failed(status_code=response.status_code):
                raise ServerException(response.status_code)
            else:
                res = response.json()
                translation = res.get("translatedText")
                if not translation:
                    raise TranslationNotFound(text)
                return translation
