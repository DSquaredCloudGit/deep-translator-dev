__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

import os

from deep_translator.base import BaseTranslator
from deep_translator.constants import GEMINI_ENV_VAR
from deep_translator.exceptions import ApiKeyException


class GeminiTranslator(BaseTranslator):
    """
    class that wraps functions, which use the Google Gemini API
    under the hood to translate word(s)
    """

    def __init__(
        self,
        source: str = "auto",
        target: str = "english",
        api_key: str | None = None,
        model: str = "gemini-2.0-flash",
        **kwargs,
    ):
        """
        @param api_key: your Google Gemini api key.
        @param source: source language to translate from
        @param target: target language to translate to
        @param model: the Gemini model to use
        """
        if api_key is None:
            api_key = os.getenv(GEMINI_ENV_VAR)

        if not api_key:
            raise ApiKeyException(env_var=GEMINI_ENV_VAR)

        self.api_key = api_key
        self.model = model

        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        self._genai_model = genai.GenerativeModel(self.model)

        super().__init__(source=source, target=target, **kwargs)

    def translate(self, text: str, **kwargs) -> str:
        """
        @param text: text to translate
        @return: translated text
        """
        prompt = (
            f"Translate the following text from {self.source} to "
            f"{self.target}. Return ONLY the translated text, "
            f"no explanations or additional text.\n\n"
            f'Text: "{text}"'
        )

        response = self._genai_model.generate_content(prompt)

        return response.text.strip().strip('"')
