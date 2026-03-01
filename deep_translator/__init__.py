"""Top-level package for Deep Translator"""

__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

from deep_translator.baidu import BaiduTranslator
from deep_translator.chatgpt import ChatGptTranslator
from deep_translator.claude import ClaudeTranslator
from deep_translator.deepl import DeeplTranslator
from deep_translator.detection import batch_detection, single_detection
from deep_translator.eunoia import EunoiaTranslator
from deep_translator.gemini import GeminiTranslator
from deep_translator.google import GoogleTranslator
from deep_translator.libre import LibreTranslator
from deep_translator.linguee import LingueeTranslator
from deep_translator.microsoft import MicrosoftTranslator
from deep_translator.mymemory import MyMemoryTranslator
from deep_translator.papago import PapagoTranslator
from deep_translator.pons import PonsTranslator
from deep_translator.qcri import QcriTranslator
from deep_translator.tencent import TencentTranslator
from deep_translator.yandex import YandexTranslator

__author__ = """Nidhal Baccouri"""
__email__ = "nidhalbacc@gmail.com"
__version__ = "1.11.4"

__all__ = [
    "GoogleTranslator",
    "PonsTranslator",
    "LingueeTranslator",
    "MyMemoryTranslator",
    "YandexTranslator",
    "MicrosoftTranslator",
    "QcriTranslator",
    "DeeplTranslator",
    "LibreTranslator",
    "PapagoTranslator",
    "ChatGptTranslator",
    "GeminiTranslator",
    "ClaudeTranslator",
    "EunoiaTranslator",
    "TencentTranslator",
    "BaiduTranslator",
    "single_detection",
    "batch_detection",
]
