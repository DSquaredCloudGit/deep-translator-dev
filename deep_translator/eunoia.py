"""Eunoia Translator - Offline ONNX-powered translation using Helsinki-NLP OPUS-MT models"""

__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from deep_translator.base import BaseTranslator
from deep_translator.constants import (
    OPUS_MT_LANGUAGES_TO_CODES,
    OPUS_MT_MULTI_TARGET_GROUPS,
)
from deep_translator.exceptions import (
    ModelDownloadException,
    ModelNotAvailableException,
)

logger = logging.getLogger(__name__)


class EunoiaTranslator(BaseTranslator):
    """
    Offline neural machine translation powered by ONNX Runtime
    using Helsinki-NLP OPUS-MT (MarianMT) models.

    Models are downloaded on-demand from Hugging Face Hub,
    converted to ONNX format, and cached locally. Supports
    INT8/INT4 quantization for optimized CPU inference.

    When a direct source→target model is unavailable,
    translation pivots through English automatically.

    Example usage:
        >>> translator = EunoiaTranslator(source="en", target="de")
        >>> translator.translate("Hello world")
        'Hallo Welt'

    Installation:
        pip install deep-translator[onnx]
    """

    _model_cache: Dict[str, Tuple] = {}

    def __init__(
        self,
        source: str = "english",
        target: str = "german",
        model_cache_dir: Optional[str] = None,
        quantization: str = "int8",
        max_length: int = 512,
        **kwargs,
    ):
        """
        @param source: source language to translate from
        @param target: target language to translate to
        @param model_cache_dir: directory to cache downloaded models
            (defaults to '.ai_models' in the current working directory)
        @param quantization: quantization level for ONNX models.
            Options: 'int8' (default), 'int4', 'none' (full precision)
        @param max_length: maximum token length for translation
        """
        if quantization not in ("int8", "int4", "none"):
            raise ValueError(
                f"Invalid quantization '{quantization}'. "
                f"Must be one of: 'int8', 'int4', 'none'"
            )

        self.model_cache_dir = Path(
            model_cache_dir or os.path.join(os.getcwd(), ".ai_models")
        )
        self.quantization = quantization
        self.max_length = max_length

        self._model = None
        self._tokenizer = None
        self._pivot_model = None
        self._pivot_tokenizer = None
        self._pivot_through_english = False
        self._model_id = None
        self._pivot_model_id = None

        super().__init__(
            source=source,
            target=target,
            languages=OPUS_MT_LANGUAGES_TO_CODES,
            **kwargs,
        )

    def _resolve_model_id(
        self, src_code: str, tgt_code: str
    ) -> Optional[str]:
        """
        Resolve the Hugging Face model ID for a given language pair.
        Tries direct pair first, then multi-target group models.

        @param src_code: source language ISO code
        @param tgt_code: target language ISO code
        @return: model ID string or None if not found
        """
        # Try direct pair model
        direct_id = f"Helsinki-NLP/opus-mt-{src_code}-{tgt_code}"

        # Check if direct model exists by trying to resolve it
        if self._check_model_exists(direct_id):
            return direct_id

        # Try multi-target group models
        for group_name, group_codes in OPUS_MT_MULTI_TARGET_GROUPS.items():
            if tgt_code in group_codes:
                group_id = (
                    f"Helsinki-NLP/opus-mt-{src_code}-{group_name}"
                )
                if self._check_model_exists(group_id):
                    return group_id

        return None

    def _check_model_exists(self, model_id: str) -> bool:
        """
        Check if a model exists on Hugging Face Hub or in local cache.

        @param model_id: the Hugging Face model identifier
        @return: True if the model exists
        """
        # Check local cache first
        cache_path = self._get_cache_path(model_id)
        if cache_path.exists() and any(cache_path.iterdir()):
            return True

        # Check Hugging Face Hub
        try:
            from huggingface_hub import model_info

            model_info(model_id)
            return True
        except Exception:
            return False

    def _get_cache_path(self, model_id: str) -> Path:
        """
        Get the local cache directory path for a model.

        @param model_id: the Hugging Face model identifier
        @return: Path to the cache directory
        """
        model_name = model_id.replace("/", "--")
        quant_suffix = (
            f"-{self.quantization}" if self.quantization != "none" else ""
        )
        return self.model_cache_dir / f"{model_name}{quant_suffix}"

    def _setup_translation_pipeline(self) -> None:
        """
        Resolve model IDs and determine if English pivot is needed.
        Called lazily on first translate() call.
        """
        src = self._source
        tgt = self._target

        if src == "auto":
            # For auto-detection with ONNX, default to English as source
            logger.warning(
                "Auto-detection not supported for ONNX translator. "
                "Defaulting source to 'en'."
            )
            src = "en"
            self._source = "en"

        # Try direct or group model
        self._model_id = self._resolve_model_id(src, tgt)

        if self._model_id:
            self._pivot_through_english = False
            logger.info(f"Using direct model: {self._model_id}")
        else:
            # Pivot through English
            if src == "en" or tgt == "en":
                raise ModelNotAvailableException(
                    f"{src}-{tgt}",
                    message=(
                        f"No OPUS-MT model found for {src} -> {tgt} "
                        f"and English pivot is not possible."
                    ),
                )

            src_to_en = self._resolve_model_id(src, "en")
            en_to_tgt = self._resolve_model_id("en", tgt)

            if not src_to_en or not en_to_tgt:
                missing = []
                if not src_to_en:
                    missing.append(f"{src}->en")
                if not en_to_tgt:
                    missing.append(f"en->{tgt}")
                raise ModelNotAvailableException(
                    f"{src}-{tgt}",
                    message=(
                        f"No direct model for {src} -> {tgt} and "
                        f"pivot models not available: {', '.join(missing)}"
                    ),
                )

            self._model_id = src_to_en
            self._pivot_model_id = en_to_tgt
            self._pivot_through_english = True
            logger.info(
                f"Using English pivot: {self._model_id} -> "
                f"{self._pivot_model_id}"
            )

    def _load_model(
        self, model_id: str
    ) -> Tuple:
        """
        Load or download and convert an OPUS-MT model to ONNX format.
        Applies quantization if configured.

        @param model_id: Hugging Face model identifier
        @return: tuple of (model, tokenizer)
        """
        # Check class-level cache
        cache_key = f"{model_id}-{self.quantization}"
        if cache_key in EunoiaTranslator._model_cache:
            logger.info(f"Loading model from memory cache: {model_id}")
            return EunoiaTranslator._model_cache[cache_key]

        cache_path = self._get_cache_path(model_id)

        try:
            from optimum.onnxruntime import ORTModelForSeq2SeqLM
            from transformers import AutoTokenizer
        except ImportError as e:
            raise ImportError(
                "The [onnx] extra is required for EunoiaTranslator. "
                "Install it with: pip install deep-translator[onnx]"
            ) from e

        try:
            if cache_path.exists() and any(cache_path.iterdir()):
                # Load from local cache
                logger.info(
                    f"Loading cached ONNX model from {cache_path}"
                )
                model = ORTModelForSeq2SeqLM.from_pretrained(
                    str(cache_path)
                )
                tokenizer = AutoTokenizer.from_pretrained(
                    str(cache_path)
                )
            else:
                # Download and convert to ONNX
                logger.info(
                    f"Downloading and converting model: {model_id}"
                )
                cache_path.mkdir(parents=True, exist_ok=True)

                model = ORTModelForSeq2SeqLM.from_pretrained(
                    model_id, export=True
                )
                tokenizer = AutoTokenizer.from_pretrained(model_id)

                # Apply quantization
                if self.quantization != "none":
                    model = self._quantize_model(
                        model, model_id, cache_path
                    )

                # Save to cache
                model.save_pretrained(str(cache_path))
                tokenizer.save_pretrained(str(cache_path))
                logger.info(f"Model cached to {cache_path}")

        except ImportError:
            raise
        except Exception as e:
            raise ModelDownloadException(
                model_id,
                message=f"Failed to load model {model_id}: {str(e)}",
            ) from e

        result = (model, tokenizer)
        EunoiaTranslator._model_cache[cache_key] = result
        return result

    def _quantize_model(self, model, model_id: str, cache_path: Path):
        """
        Apply ONNX quantization to the model.

        @param model: the ONNX model to quantize
        @param model_id: model identifier for logging
        @param cache_path: path to save quantized model
        @return: quantized model
        """
        try:
            from optimum.onnxruntime import ORTModelForSeq2SeqLM
            from optimum.onnxruntime.configuration import (
                AutoQuantizationConfig,
            )
            from optimum.onnxruntime import ORTQuantizer

            if self.quantization == "int8":
                qconfig = AutoQuantizationConfig.avx512_vnni(
                    is_static=False
                )
            elif self.quantization == "int4":
                qconfig = AutoQuantizationConfig.arm64(
                    is_static=False
                )
            else:
                return model

            logger.info(
                f"Applying {self.quantization} quantization to {model_id}"
            )

            # Quantize encoder and decoder separately
            encoder_quantizer = ORTQuantizer.from_pretrained(
                model_id, file_name="encoder_model.onnx"
            )
            decoder_quantizer = ORTQuantizer.from_pretrained(
                model_id, file_name="decoder_model.onnx"
            )

            encoder_quantizer.quantize(
                save_dir=str(cache_path),
                quantization_config=qconfig,
            )
            decoder_quantizer.quantize(
                save_dir=str(cache_path),
                quantization_config=qconfig,
            )

            # Reload quantized model
            model = ORTModelForSeq2SeqLM.from_pretrained(
                str(cache_path)
            )

            logger.info(
                f"Quantization ({self.quantization}) applied successfully"
            )
            return model

        except Exception as e:
            logger.warning(
                f"Quantization failed for {model_id}, "
                f"using unquantized model: {e}"
            )
            return model

    def _ensure_models_loaded(self) -> None:
        """
        Lazily load models on first use. Sets up the translation pipeline
        and loads the ONNX model(s) into memory.
        """
        if self._model is not None:
            return

        self._setup_translation_pipeline()
        self._model, self._tokenizer = self._load_model(self._model_id)

        if self._pivot_through_english and self._pivot_model_id:
            self._pivot_model, self._pivot_tokenizer = self._load_model(
                self._pivot_model_id
            )

    def _translate_single(
        self, text: str, model, tokenizer
    ) -> str:
        """
        Perform a single translation using the given model and tokenizer.

        @param text: text to translate
        @param model: ONNX model for inference
        @param tokenizer: tokenizer for the model
        @return: translated text
        """
        inputs = tokenizer(
            text,
            return_tensors="pt",
            max_length=self.max_length,
            truncation=True,
            padding=True,
        )

        outputs = model.generate(
            **inputs,
            max_length=self.max_length,
        )

        translated = tokenizer.batch_decode(
            outputs, skip_special_tokens=True
        )

        return translated[0] if translated else ""

    def translate(self, text: str, **kwargs) -> str:
        """
        Translate text using the ONNX model.
        Models are loaded lazily on first call.

        @param text: text to translate
        @return: translated text
        """
        if not text or not text.strip():
            return text

        if self._same_source_target():
            return text

        self._ensure_models_loaded()

        if self._pivot_through_english:
            # Two-step translation: source -> English -> target
            intermediate = self._translate_single(
                text, self._model, self._tokenizer
            )
            return self._translate_single(
                intermediate, self._pivot_model, self._pivot_tokenizer
            )
        else:
            return self._translate_single(
                text, self._model, self._tokenizer
            )

    def translate_file(self, path: str, **kwargs) -> str:
        """
        translate from a file
        @param path: path to the target file
        @return: translated text
        """
        return self._translate_file(path, **kwargs)

    def translate_batch(self, batch: List[str], **kwargs) -> List[str]:
        """
        Translate a batch of texts. Uses batched inference for efficiency
        when not pivoting through English.

        @param batch: list of texts to translate
        @return: list of translations
        """
        if not batch:
            raise Exception(
                "Enter your text list that you want to translate"
            )

        self._ensure_models_loaded()

        if self._pivot_through_english:
            # Pivot requires sequential two-step for each item
            return self._translate_batch(batch, **kwargs)

        # Batched inference for direct translation
        inputs = self._tokenizer(
            batch,
            return_tensors="pt",
            max_length=self.max_length,
            truncation=True,
            padding=True,
        )

        outputs = self._model.generate(
            **inputs,
            max_length=self.max_length,
        )

        return self._tokenizer.batch_decode(
            outputs, skip_special_tokens=True
        )

    @classmethod
    def clear_model_cache(cls) -> None:
        """
        Clear all models from memory cache.
        Useful for freeing GPU/CPU memory.
        """
        cls._model_cache.clear()
        logger.info("Model memory cache cleared")

    @classmethod
    def get_cached_models(cls) -> List[str]:
        """
        Get list of model IDs currently loaded in memory cache.

        @return: list of cache keys
        """
        return list(cls._model_cache.keys())
