__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

import os
from typing import List, Optional

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
        api_key: Optional[str] = os.getenv(GEMINI_ENV_VAR, None),
        model: Optional[str] = "gemini-2.0-flash",
        **kwargs,
    ):
        """
        @param api_key: your Google Gemini api key.
        @param source: source language to translate from
        @param target: target language to translate to
        @param model: the Gemini model to use
        """
        if not api_key:
            raise ApiKeyException(env_var=GEMINI_ENV_VAR)

        self.api_key = api_key
        self.model = model

        super().__init__(source=source, target=target, **kwargs)

    def translate(self, text: str, **kwargs) -> str:
        """
        @param text: text to translate
        @return: translated text
        """
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)

        model = genai.GenerativeModel(self.model)

        prompt = (
            f"Translate the following text from {self.source} to "
            f"{self.target}. Return ONLY the translated text, "
            f"no explanations or additional text.\n\n"
            f'Text: "{text}"'
        )

        response = model.generate_content(prompt)

        return response.text.strip().strip('"')

    def translate_file(self, path: str, **kwargs) -> str:
        """
        translate from a file
        @param path: path to the target file
        @return: translated text
        """
        return self._translate_file(path, **kwargs)

    def translate_batch(self, batch: List[str], **kwargs) -> List[str]:
        """
        @param batch: list of texts to translate
        @return: list of translations
        """
        return self._translate_batch(batch, **kwargs)
