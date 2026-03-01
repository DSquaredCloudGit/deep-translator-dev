"""Tests for EunoiaTranslator (ONNX-powered offline translation)."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path

from deep_translator import EunoiaTranslator
from deep_translator.constants import (
    OPUS_MT_LANGUAGES_TO_CODES,
    OPUS_MT_MULTI_TARGET_GROUPS,
)
from deep_translator.exceptions import (
    ModelDownloadException,
    ModelNotAvailableException,
)


class TestEunoiaTranslatorInit:
    """Test EunoiaTranslator initialization."""

    def test_default_init(self):
        """Test default constructor values."""
        translator = EunoiaTranslator()
        assert translator._source == "en"
        assert translator._target == "de"
        assert translator.quantization == "int8"
        assert translator.max_length == 512
        assert translator._model is None

    def test_custom_init(self):
        """Test custom constructor values."""
        translator = EunoiaTranslator(
            source="french",
            target="spanish",
            quantization="int4",
            max_length=256,
        )
        assert translator._source == "fr"
        assert translator._target == "es"
        assert translator.quantization == "int4"
        assert translator.max_length == 256

    def test_invalid_quantization(self):
        """Test that invalid quantization raises ValueError."""
        with pytest.raises(ValueError, match="Invalid quantization"):
            EunoiaTranslator(quantization="int16")

    def test_invalid_language(self):
        """Test that unsupported language raises exception."""
        with pytest.raises(Exception):
            EunoiaTranslator(source="klingon", target="german")

    def test_language_mapping(self):
        """Test that all OPUS-MT languages are supported."""
        translator = EunoiaTranslator()
        languages = translator.get_supported_languages(as_dict=True)
        assert languages == OPUS_MT_LANGUAGES_TO_CODES

    def test_custom_cache_dir(self, tmp_path):
        """Test custom model cache directory."""
        cache_dir = str(tmp_path / "models")
        translator = EunoiaTranslator(model_cache_dir=cache_dir)
        assert translator.model_cache_dir == Path(cache_dir)


class TestModelResolution:
    """Test model ID resolution logic."""

    def test_resolve_direct_model(self):
        """Test resolving a direct language pair model."""
        translator = EunoiaTranslator(source="english", target="german")
        with patch.object(
            translator, "_check_model_exists", return_value=True
        ):
            model_id = translator._resolve_model_id("en", "de")
            assert model_id == "Helsinki-NLP/opus-mt-en-de"

    def test_resolve_group_model(self):
        """Test resolving a multi-target group model."""
        translator = EunoiaTranslator(source="english", target="french")

        def mock_check(model_id):
            # Direct model doesn't exist, but group model does
            return "ROMANCE" in model_id

        with patch.object(
            translator, "_check_model_exists", side_effect=mock_check
        ):
            model_id = translator._resolve_model_id("en", "fr")
            assert model_id == "Helsinki-NLP/opus-mt-en-ROMANCE"

    def test_resolve_no_model(self):
        """Test that None is returned when no model exists."""
        translator = EunoiaTranslator(source="english", target="german")
        with patch.object(
            translator, "_check_model_exists", return_value=False
        ):
            model_id = translator._resolve_model_id("en", "xx")
            assert model_id is None


class TestTranslationPipeline:
    """Test the translation pipeline setup."""

    def test_direct_translation_setup(self):
        """Test pipeline setup for direct translation."""
        translator = EunoiaTranslator(source="english", target="german")
        with patch.object(
            translator,
            "_resolve_model_id",
            return_value="Helsinki-NLP/opus-mt-en-de",
        ):
            translator._setup_translation_pipeline()
            assert not translator._pivot_through_english
            assert translator._model_id == "Helsinki-NLP/opus-mt-en-de"

    def test_pivot_translation_setup(self):
        """Test pipeline setup with English pivot."""
        translator = EunoiaTranslator(source="french", target="japanese")

        def mock_resolve(src, tgt):
            if src == "fr" and tgt == "ja":
                return None  # No direct model
            if src == "fr" and tgt == "en":
                return "Helsinki-NLP/opus-mt-fr-en"
            if src == "en" and tgt == "ja":
                return "Helsinki-NLP/opus-mt-en-ja"
            return None

        with patch.object(
            translator, "_resolve_model_id", side_effect=mock_resolve
        ):
            translator._setup_translation_pipeline()
            assert translator._pivot_through_english
            assert translator._model_id == "Helsinki-NLP/opus-mt-fr-en"
            assert (
                translator._pivot_model_id
                == "Helsinki-NLP/opus-mt-en-ja"
            )

    def test_no_model_available_raises(self):
        """Test that missing models raise ModelNotAvailableException."""
        translator = EunoiaTranslator(source="english", target="german")
        with patch.object(
            translator, "_resolve_model_id", return_value=None
        ):
            with pytest.raises(ModelNotAvailableException):
                translator._setup_translation_pipeline()

    def test_auto_source_defaults_to_english(self):
        """Test that 'auto' source defaults to 'en'."""
        translator = EunoiaTranslator(source="english", target="german")
        translator._source = "auto"
        with patch.object(
            translator,
            "_resolve_model_id",
            return_value="Helsinki-NLP/opus-mt-en-de",
        ):
            translator._setup_translation_pipeline()
            assert translator._source == "en"


class TestTranslation:
    """Test translate method with mocked models."""

    @patch(
        "deep_translator.eunoia.EunoiaTranslator._ensure_models_loaded"
    )
    def test_translate_empty_text(self, mock_load):
        """Test that empty text returns empty text."""
        translator = EunoiaTranslator()
        assert translator.translate("") == ""
        assert translator.translate("   ") == "   "

    @patch(
        "deep_translator.eunoia.EunoiaTranslator._ensure_models_loaded"
    )
    def test_translate_same_source_target(self, mock_load):
        """Test that same source/target returns original text."""
        translator = EunoiaTranslator(
            source="english", target="english"
        )
        assert translator.translate("Hello") == "Hello"

    def test_translate_with_mock_model(self):
        """Test translation with mocked ONNX model."""
        translator = EunoiaTranslator()

        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {"input_ids": MagicMock()}
        mock_tokenizer.batch_decode.return_value = ["Hallo Welt"]

        mock_model = MagicMock()
        mock_model.generate.return_value = MagicMock()

        translator._model = mock_model
        translator._tokenizer = mock_tokenizer

        with patch.object(
            translator, "_ensure_models_loaded"
        ):
            result = translator._translate_single(
                "Hello world", mock_model, mock_tokenizer
            )
            assert result == "Hallo Welt"

    def test_translate_batch_with_mock_model(self):
        """Test batch translation with mocked ONNX model."""
        translator = EunoiaTranslator()

        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {"input_ids": MagicMock()}
        mock_tokenizer.batch_decode.return_value = [
            "Hallo",
            "Welt",
        ]

        mock_model = MagicMock()
        mock_model.generate.return_value = MagicMock()

        translator._model = mock_model
        translator._tokenizer = mock_tokenizer
        translator._pivot_through_english = False

        with patch.object(translator, "_ensure_models_loaded"):
            results = translator.translate_batch(["Hello", "World"])
            assert results == ["Hallo", "Welt"]


class TestCacheManagement:
    """Test model cache management."""

    def test_clear_model_cache(self):
        """Test clearing the model memory cache."""
        EunoiaTranslator._model_cache["test-key"] = (
            MagicMock(),
            MagicMock(),
        )
        EunoiaTranslator.clear_model_cache()
        assert len(EunoiaTranslator._model_cache) == 0

    def test_get_cached_models(self):
        """Test listing cached model keys."""
        EunoiaTranslator._model_cache.clear()
        EunoiaTranslator._model_cache["model-a-int8"] = (
            MagicMock(),
            MagicMock(),
        )
        EunoiaTranslator._model_cache["model-b-int4"] = (
            MagicMock(),
            MagicMock(),
        )
        cached = EunoiaTranslator.get_cached_models()
        assert "model-a-int8" in cached
        assert "model-b-int4" in cached
        EunoiaTranslator._model_cache.clear()

    def test_cache_path_with_quantization(self, tmp_path):
        """Test cache path includes quantization suffix."""
        translator = EunoiaTranslator(
            model_cache_dir=str(tmp_path), quantization="int8"
        )
        path = translator._get_cache_path(
            "Helsinki-NLP/opus-mt-en-de"
        )
        assert "int8" in str(path)

    def test_cache_path_without_quantization(self, tmp_path):
        """Test cache path without quantization suffix."""
        translator = EunoiaTranslator(
            model_cache_dir=str(tmp_path), quantization="none"
        )
        path = translator._get_cache_path(
            "Helsinki-NLP/opus-mt-en-de"
        )
        assert "int8" not in str(path)
        assert "int4" not in str(path)
