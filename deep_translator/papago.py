"""Papago translator API"""

__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

from deep_translator.base import BaseTranslator
from deep_translator.constants import (
    BASE_URLS,
    DEFAULT_TIMEOUT,
    PAPAGO_LANGUAGE_TO_CODE,
)
from deep_translator.exceptions import (
    ApiKeyException,
    ServerException,
    TranslationNotFound,
)
from deep_translator.validate import is_input_valid, request_failed


class PapagoTranslator(BaseTranslator):
    """
    class that wraps functions, which use Naver Papago
    under the hood to translate text(s)
    """

    def __init__(
        self,
        client_id: str | None = None,
        secret_key: str | None = None,
        source: str = "auto",
        target: str = "en",
        **kwargs,
    ):
        """
        @param client_id: your Naver Papago client ID
        @param secret_key: your Naver Papago secret key
        @param source: source language to translate from
        @param target: target language to translate to
        """
        if not client_id or not secret_key:
            raise ApiKeyException(
                env_var="PAPAGO_CLIENT_ID / PAPAGO_SECRET_KEY"
            )

        self.client_id = client_id
        self.secret_key = secret_key
        super().__init__(
            base_url=BASE_URLS.get("PAPAGO_API"),
            source=source,
            target=target,
            languages=PAPAGO_LANGUAGE_TO_CODE,
            **kwargs,
        )

    def translate(self, text: str, **kwargs) -> str:
        """
        Translate text using Naver Papago.
        @param text: desired text to translate
        @return: str: translated text
        """
        if is_input_valid(text):
            payload = {
                "source": self._source,
                "target": self._target,
                "text": text,
            }
            headers = {
                "X-Naver-Client-Id": self.client_id,
                "X-Naver-Client-Secret": self.secret_key,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            }
            session = self._get_session()
            response = session.post(
                self._base_url,
                headers=headers,
                data=payload,
                timeout=DEFAULT_TIMEOUT,
            )
            if request_failed(status_code=response.status_code):
                raise ServerException(response.status_code)
            res_body = response.json()
            if "message" not in res_body:
                raise TranslationNotFound(text)

            msg = res_body.get("message")
            result = msg.get("result", None)
            if not result:
                raise TranslationNotFound(text)
            return result.get("translatedText")
