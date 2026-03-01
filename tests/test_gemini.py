"""Tests for GeminiTranslator."""

import pytest
from unittest.mock import patch, MagicMock

from deep_translator.exceptions import ApiKeyException


class TestGeminiTranslatorInit:
    """Test GeminiTranslator initialization."""

    def test_missing_api_key_raises(self):
        """Test that missing API key raises ApiKeyException."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ApiKeyException):
                from deep_translator import GeminiTranslator

                GeminiTranslator(api_key=None)

    def test_init_with_api_key(self):
        """Test initialization with valid API key."""
        from deep_translator import GeminiTranslator

        translator = GeminiTranslator(
            api_key="test-key-123",
            target="german",
        )
        assert translator.api_key == "test-key-123"
        assert translator._target == "de"

    def test_default_model(self):
        """Test default model is gemini-2.0-flash."""
        from deep_translator import GeminiTranslator

        translator = GeminiTranslator(api_key="test-key")
        assert translator.model == "gemini-2.0-flash"

    def test_custom_model(self):
        """Test custom model setting."""
        from deep_translator import GeminiTranslator

        translator = GeminiTranslator(
            api_key="test-key", model="gemini-pro"
        )
        assert translator.model == "gemini-pro"

    def test_invalid_source_target(self):
        """Test invalid languages raise exceptions."""
        from deep_translator import GeminiTranslator

        with pytest.raises(Exception):
            GeminiTranslator(
                api_key="key", source="", target=""
            )

    @patch("deep_translator.gemini.genai", create=True)
    def test_translate_mocked(self, mock_genai):
        """Test translation with mocked Gemini API."""
        from deep_translator import GeminiTranslator

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '"Hallo Welt"'
        mock_model.generate_content.return_value = mock_response

        with patch(
            "google.generativeai.configure"
        ) as mock_configure, patch(
            "google.generativeai.GenerativeModel",
            return_value=mock_model,
        ):
            translator = GeminiTranslator(
                api_key="test-key", source="english", target="german"
            )
            result = translator.translate("Hello world")
            assert result == "Hallo Welt"

    def test_translate_file(self, tmp_path):
        """Test translate_file delegates to _translate_file."""
        from deep_translator import GeminiTranslator

        translator = GeminiTranslator(
            api_key="test-key", target="german"
        )
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello")

        with patch.object(
            translator, "translate", return_value="Hallo"
        ):
            result = translator.translate_file(str(test_file))
            assert result == "Hallo"

    def test_translate_batch(self):
        """Test translate_batch delegates to _translate_batch."""
        from deep_translator import GeminiTranslator

        translator = GeminiTranslator(
            api_key="test-key", target="german"
        )

        with patch.object(
            translator,
            "translate",
            side_effect=["Hallo", "Welt"],
        ):
            results = translator.translate_batch(
                ["Hello", "World"]
            )
            assert results == ["Hallo", "Welt"]
