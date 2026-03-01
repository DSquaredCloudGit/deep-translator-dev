__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

import os

from deep_translator.base import BaseTranslator
from deep_translator.constants import OPEN_AI_ENV_VAR
from deep_translator.exceptions import ApiKeyException


class ChatGptTranslator(BaseTranslator):
    """
    class that wraps functions, which use the ChatGPT
    under the hood to translate word(s)
    """

    def __init__(
        self,
        source: str = "auto",
        target: str = "english",
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        **kwargs,
    ):
        """
        @param api_key: your openai api key.
        @param source: source language
        @param target: target language
        @param model: the OpenAI model to use
        """
        if api_key is None:
            api_key = os.getenv(OPEN_AI_ENV_VAR)

        if not api_key:
            raise ApiKeyException(env_var=OPEN_AI_ENV_VAR)

        self.api_key = api_key
        self.model = model

        import openai

        self._client = openai.OpenAI(api_key=self.api_key)

        super().__init__(source=source, target=target, **kwargs)

    def translate(self, text: str, **kwargs) -> str:
        """
        @param text: text to translate
        @return: translated text
        """
        prompt = f"Translate the text below into {self.target}.\n"
        prompt += f'Text: "{text}"'

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response.choices[0].message.content
