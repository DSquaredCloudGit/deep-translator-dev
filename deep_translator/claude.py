__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

import os
from typing import List, Optional

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
        api_key: Optional[str] = os.getenv(ANTHROPIC_ENV_VAR, None),
        model: Optional[str] = "claude-sonnet-4-20250514",
        **kwargs,
    ):
        """
        @param api_key: your Anthropic API key.
        @param source: source language to translate from
        @param target: target language to translate to
        @param model: the Claude model to use
        """
        if not api_key:
            raise ApiKeyException(env_var=ANTHROPIC_ENV_VAR)

        self.api_key = api_key
        self.model = model

        super().__init__(source=source, target=target, **kwargs)

    def translate(self, text: str, **kwargs) -> str:
        """
        @param text: text to translate
        @return: translated text
        """
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)

        prompt = (
            f"Translate the following text from {self.source} to "
            f"{self.target}. Return ONLY the translated text, "
            f"no explanations or additional text.\n\n"
            f'Text: "{text}"'
        )

        response = client.messages.create(
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
