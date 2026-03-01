__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

import os

from deep_translator.base import BaseTranslator
from deep_translator.constants import ANTHROPIC_ENV_VAR
from deep_translator.exceptions import ApiKeyException


class ClaudeTranslator(BaseTranslator):
    """
    class that wraps functions, which use the Anthropic Claude API
    under the hood to translate word(s)
    """

    def __init__(
        self,
        source: str = "auto",
        target: str = "english",
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
        **kwargs,
    ):
        """
        @param api_key: your Anthropic API key.
        @param source: source language to translate from
        @param target: target language to translate to
        @param model: the Claude model to use
        """
        if api_key is None:
            api_key = os.getenv(ANTHROPIC_ENV_VAR)

        if not api_key:
            raise ApiKeyException(env_var=ANTHROPIC_ENV_VAR)

        self.api_key = api_key
        self.model = model

        import anthropic

        self._client = anthropic.Anthropic(api_key=self.api_key)

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

        response = self._client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response.content[0].text.strip().strip('"')
