"""base translator class"""

__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

from abc import ABC, abstractmethod
from pathlib import Path

import requests

from deep_translator.constants import DEFAULT_TIMEOUT, GOOGLE_LANGUAGES_TO_CODES
from deep_translator.exceptions import (
    InvalidSourceOrTargetLanguage,
    LanguageNotSupportedException,
    NotValidPayload,
)
from deep_translator.validate import is_empty, is_input_valid


class BaseTranslator(ABC):
    """
    Abstract class that serves as a base translator for other different translators.
    """

    def __init__(
        self,
        base_url: str | None = None,
        languages: dict = GOOGLE_LANGUAGES_TO_CODES,
        source: str = "auto",
        target: str = "en",
        payload_key: str | None = None,
        element_tag: str | None = None,
        element_query: dict | None = None,
        **url_params,
    ):
        """
        @param source: source language to translate from
        @param target: target language to translate to
        """
        self._base_url = base_url
        self._languages = languages
        self._supported_languages = list(self._languages.keys())
        if not source:
            raise InvalidSourceOrTargetLanguage(source)
        if not target:
            raise InvalidSourceOrTargetLanguage(target)

        self._source, self._target = self._map_language_to_code(source, target)
        self._url_params = url_params
        self._element_tag = element_tag
        self._element_query = element_query
        self.payload_key = payload_key

        # HTTP session for connection pooling (used by HTTP-based translators)
        self._session: requests.Session | None = None

        super().__init__()

    # ------------------------------------------------------------------ #
    #  Context manager support                                            #
    # ------------------------------------------------------------------ #

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def close(self) -> None:
        """Close the underlying HTTP session, if any."""
        if self._session is not None:
            self._session.close()
            self._session = None

    # ------------------------------------------------------------------ #
    #  HTTP session (lazy-created)                                        #
    # ------------------------------------------------------------------ #

    def _get_session(self) -> requests.Session:
        """Return the shared requests.Session, creating it on first use."""
        if self._session is None:
            self._session = requests.Session()
        return self._session

    # ------------------------------------------------------------------ #
    #  Properties                                                         #
    # ------------------------------------------------------------------ #

    @property
    def source(self) -> str:
        return self._source

    @source.setter
    def source(self, lang: str) -> None:
        self._source = lang

    @property
    def target(self) -> str:
        return self._target

    @target.setter
    def target(self, lang: str) -> None:
        self._target = lang

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(source='{self._source}', target='{self._target}')"

    def _type(self) -> str:
        return self.__class__.__name__

    def _map_language_to_code(self, *languages: str) -> tuple[str, ...]:
        """
        Map language to its corresponding code (abbreviation) if the language
        was passed by its full name by the user.

        @param languages: list of languages
        @return: tuple of mapped language codes
        """
        result: list[str] = []
        for language in languages:
            if language in self._languages.values() or language == "auto":
                result.append(language)
            elif language in self._languages.keys():
                result.append(self._languages[language])
            else:
                raise LanguageNotSupportedException(
                    language,
                    message=f"No support for the provided language.\n"
                    f"Please select one of the supported languages:\n"
                    f"{self._languages}",
                )
        return tuple(result)

    def _same_source_target(self) -> bool:
        return self._source == self._target

    def _pre_translate_check(
        self, text: str, max_chars: int | None = None
    ) -> str | None:
        """
        Common pre-translation validation.
        Returns the text unchanged if source == target or text is empty,
        or None if translation should proceed.
        Raises on invalid input.
        """
        if is_input_valid(text, max_chars=max_chars):
            text = text.strip()
            if self._same_source_target() or is_empty(text):
                return text
        return None

    def get_supported_languages(
        self, as_dict: bool = False, **kwargs
    ) -> list | dict:
        """
        Return the supported languages by this translator.

        @param as_dict: if True, return a dictionary mapping languages to codes
        @return: list or dict
        """
        return self._supported_languages if not as_dict else self._languages

    def is_language_supported(self, language: str, **kwargs) -> bool:
        """
        Check if the language is supported by the translator.

        @param language: a string for 1 language
        @return: bool
        """
        return (
            language == "auto"
            or language in self._languages.keys()
            or language in self._languages.values()
        )

    @abstractmethod
    def translate(self, text: str, **kwargs) -> str:
        """
        Translate a text using the translator and return the translated text.

        @param text: text to translate
        @param kwargs: additional arguments
        @return: str
        """
        raise NotImplementedError("You need to implement the translate method!")

    def _read_docx(self, f: str) -> str:
        import docx2txt

        return docx2txt.process(f)

    def _read_pdf(self, f: str) -> str:
        import pypdf

        reader = pypdf.PdfReader(f)
        page = reader.pages[0]
        return page.extract_text()

    def _translate_file(self, path: str, **kwargs) -> str:
        """
        Translate directly from file.

        @param path: path to the target file
        @return: translated text
        """
        if not isinstance(path, Path):
            path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        ext = path.suffix

        if ext == ".docx":
            text = self._read_docx(f=str(path))
        elif ext == ".pdf":
            text = self._read_pdf(f=str(path))
        else:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read().strip()

        return self.translate(text)

    def translate_file(self, path: str, **kwargs) -> str:
        """
        Translate directly from file.

        @param path: path to the target file
        @return: translated text
        """
        return self._translate_file(path, **kwargs)

    def _translate_batch(self, batch: list[str], **kwargs) -> list[str]:
        """
        Translate a list of texts.

        @param batch: list of texts you want to translate
        @return: list of translations
        """
        if not batch:
            raise NotValidPayload(
                batch, message="Batch must be a non-empty list of strings"
            )
        return [self.translate(text, **kwargs) for text in batch]

    def translate_batch(self, batch: list[str], **kwargs) -> list[str]:
        """
        Translate a list of texts.

        @param batch: list of texts you want to translate
        @return: list of translations
        """
        return self._translate_batch(batch, **kwargs)
