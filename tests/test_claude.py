"""Tests for ClaudeTranslator."""

import pytest
from unittest.mock import patch, MagicMock

from deep_translator.exceptions import ApiKeyException


class TestClaudeTranslatorInit:
    """Test ClaudeTranslator initialization."""

    def test_missing_api_key_raises(self):
        """Test that missing API key raises ApiKeyException."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ApiKeyException):
                from deep_translator import ClaudeTranslator

                ClaudeTranslator(api_key=None)

    def test_init_with_api_key(self):
        """Test initialization with valid API key."""
        from deep_translator import ClaudeTranslator

        translator = ClaudeTranslator(
            api_key="test-key-123",
            target="german",
        )
        assert translator.api_key == "test-key-123"
        assert translator._target == "de"

    def test_default_model(self):
        """Test default model is claude-sonnet-4-20250514."""
        from deep_translator import ClaudeTranslator

        translator = ClaudeTranslator(api_key="test-key")
        assert translator.model == "claude-sonnet-4-20250514"

    def test_custom_model(self):
        """Test custom model setting."""
        from deep_translator import ClaudeTranslator

        translator = ClaudeTranslator(
            api_key="test-key", model="claude-3-haiku-20240307"
        )
        assert translator.model == "claude-3-haiku-20240307"

    def test_invalid_source_target(self):
        """Test invalid languages raise exceptions."""
        from deep_translator import ClaudeTranslator

        with pytest.raises(Exception):
            ClaudeTranslator(
                api_key="key", source="", target=""
            )

    def test_translate_mocked(self):
        """Test translation with mocked Anthropic API."""
        from deep_translator import ClaudeTranslator

        mock_content = MagicMock()
        mock_content.text = '"Hallo Welt"'

        mock_response = MagicMock()
        mock_response.content = [mock_content]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        with patch(
            "anthropic.Anthropic", return_value=mock_client
        ):
            translator = ClaudeTranslator(
                api_key="test-key",
                source="english",
                target="german",
            )
            result = translator.translate("Hello world")
            assert result == "Hallo Welt"

    def test_translate_file(self, tmp_path):
        """Test translate_file delegates to _translate_file."""
        from deep_translator import ClaudeTranslator

        translator = ClaudeTranslator(
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
        from deep_translator import ClaudeTranslator

        translator = ClaudeTranslator(
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
