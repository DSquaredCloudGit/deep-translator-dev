"""Tencent translator API"""

__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

import base64
import hashlib
import hmac
import os
import time

from deep_translator.base import BaseTranslator
from deep_translator.constants import (
    BASE_URLS,
    DEFAULT_TIMEOUT,
    TENCENT_LANGUAGE_TO_CODE,
    TENCENT_SECRET_ID_ENV_VAR,
    TENCENT_SECRET_KEY_ENV_VAR,
)
from deep_translator.exceptions import (
    ApiKeyException,
    ServerException,
    TencentAPIerror,
    TranslationNotFound,
)
from deep_translator.validate import is_empty, is_input_valid


class TencentTranslator(BaseTranslator):
    """
    class that wraps functions, which use the TencentTranslator
    under the hood to translate word(s)
    """

    def __init__(
        self,
        source: str = "en",
        target: str = "zh",
        secret_id: str | None = None,
        secret_key: str | None = None,
        **kwargs,
    ):
        """
        @param secret_id: your tencent cloud api secret id.
        Get one here: https://console.cloud.tencent.com/capi
        @param secret_key: your tencent cloud api secret key.
        @param source: source language
        @param target: target language
        """
        if secret_id is None:
            secret_id = os.getenv(TENCENT_SECRET_ID_ENV_VAR)
        if secret_key is None:
            secret_key = os.getenv(TENCENT_SECRET_KEY_ENV_VAR)

        if not secret_id:
            raise ApiKeyException(env_var=TENCENT_SECRET_ID_ENV_VAR)
        if not secret_key:
            raise ApiKeyException(env_var=TENCENT_SECRET_KEY_ENV_VAR)

        self.secret_id = secret_id
        self.secret_key = secret_key
        super().__init__(
            base_url=BASE_URLS.get("TENCENT"),
            source=source,
            target=target,
            languages=TENCENT_LANGUAGE_TO_CODE,
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

            translate_endpoint = self._base_url.replace("https://", "")
            params = {
                "Action": "TextTranslate",
                "Nonce": 11886,
                "ProjectId": 0,
                "Region": "ap-guangzhou",
                "SecretId": self.secret_id,
                "Source": self.source,
                "SourceText": text,
                "Target": self.target,
                "Timestamp": int(time.time()),
                "Version": "2018-03-21",
            }
            s = f"GET{translate_endpoint}/?"
            query_str = "&".join(
                f"{k}={params[k]}" for k in sorted(params)
            )
            hmac_str = hmac.new(
                self.secret_key.encode("utf8"),
                (s + query_str).encode("utf8"),
                hashlib.sha1,
            ).digest()
            params["Signature"] = base64.b64encode(hmac_str)

            try:
                session = self._get_session()
                response = session.get(
                    self._base_url,
                    params=params,
                    timeout=DEFAULT_TIMEOUT,
                )
            except ConnectionError:
                raise ServerException(503)
            if response.status_code != 200:
                raise ServerException(response.status_code)

            res = response.json()
            if not res:
                raise TranslationNotFound(text)
            if "Error" in res["Response"]:
                raise TencentAPIerror(res["Response"]["Error"]["Code"])
            return res["Response"]["TargetText"]
