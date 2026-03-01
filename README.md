# Deep Translator

A flexible Python tool to translate between different languages using multiple translation engines — including offline ONNX-powered neural machine translation and cloud AI providers (ChatGPT, Gemini, Claude).

> **Fork of [nidhaloff/deep-translator](https://github.com/nidhaloff/deep-translator)** — extended with local AI translation (Eunoia/ONNX), Gemini, and Claude support.

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Features

| Engine | Type | API Key | Offline | Notes |
|--------|------|---------|---------|-------|
| **EunoiaTranslator** | ONNX / Helsinki-NLP OPUS-MT | No | Yes | INT8/INT4 quantization, 60+ languages, auto English pivot |
| **GeminiTranslator** | Google Gemini API | Yes | No | Default: `gemini-2.0-flash` |
| **ClaudeTranslator** | Anthropic Claude API | Yes | No | Default: `claude-sonnet-4-20250514` |
| **ChatGptTranslator** | OpenAI API (v1.0+ SDK) | Yes | No | Default: `gpt-4o-mini` |
| GoogleTranslator | Web scraping | No | No | 148 languages, 5000 char limit |
| DeeplTranslator | DeepL API | Yes | No | 30 languages |
| MicrosoftTranslator | Azure Cognitive Services | Yes | No | |
| LibreTranslator | LibreTranslate API | Optional | No | Self-hostable |
| MyMemoryTranslator | MyMemory API | No | No | ~300 locales |
| PonsTranslator | Web scraping | No | No | 22 languages |
| LingueeTranslator | Web scraping | No | No | 26 languages |
| YandexTranslator | Yandex API | Yes | No | |
| PapagoTranslator | Naver Papago | Yes | No | 10 languages |
| QcriTranslator | QCRI API | Yes | No | 3 languages |
| TencentTranslator | Tencent TMT API | Yes | No | 17 languages |
| BaiduTranslator | Baidu Translate API | Yes | No | 28 languages |

---

## Installation

```bash
# Core only (Google, Pons, Linguee, MyMemory, etc.)
pip install deep-translator

# Cloud AI translators (ChatGPT + Gemini + Claude)
pip install deep-translator[ai]

# Local ONNX translator (offline, no API key)
pip install deep-translator[onnx]

# Both AI and ONNX
pip install deep-translator[ai,onnx]

# File support
pip install deep-translator[docx]      # .docx files
pip install deep-translator[pdf]       # .pdf files

# Install from this fork via GitHub
pip install git+https://github.com/nidhaloff/deep-translator.git
pip install "deep-translator[onnx] @ git+https://github.com/nidhaloff/deep-translator.git"
```

**Requires Python 3.12+**

---

## Quick Start

### EunoiaTranslator (Offline ONNX)

No API key required. Models download automatically on first use and are cached locally.

```python
from deep_translator import EunoiaTranslator

# Basic translation
translator = EunoiaTranslator(source="english", target="german")
result = translator.translate("Hello world")
# "Hallo Welt"

# Language codes work too
translator = EunoiaTranslator(source="en", target="fr")
result = translator.translate("Good morning")

# Batch translation (batched inference for efficiency)
results = translator.translate_batch(["Hello", "Goodbye", "Thank you"])

# Translate from file
result = translator.translate_file("path/to/document.txt")
```

#### Quantization

```python
# INT8 quantization (default) — good balance of speed and accuracy
translator = EunoiaTranslator(source="en", target="de", quantization="int8")

# INT4 quantization — smallest model, fastest inference
translator = EunoiaTranslator(source="en", target="de", quantization="int4")

# Full precision — maximum accuracy
translator = EunoiaTranslator(source="en", target="de", quantization="none")
```

#### Model Cache

```python
# Custom cache directory (default: .ai_models/ in working directory)
translator = EunoiaTranslator(
    source="en",
    target="de",
    model_cache_dir="/app/.ai_models",
)

# Memory management
EunoiaTranslator.get_cached_models()   # list models loaded in memory
EunoiaTranslator.clear_model_cache()   # free memory
```

#### Automatic English Pivot

When a direct model doesn't exist for a language pair (e.g., Japanese → Arabic), the translator automatically chains through English:

```python
# Automatically becomes: Japanese → English → Arabic
translator = EunoiaTranslator(source="japanese", target="arabic")
result = translator.translate("こんにちは")
```

### GeminiTranslator

```python
from deep_translator import GeminiTranslator

# Set env var: export GEMINI_API_KEY="your-key"
translator = GeminiTranslator(source="en", target="japanese")
result = translator.translate("Hello world")

# Or pass key directly
translator = GeminiTranslator(
    api_key="your-key",
    source="english",
    target="french",
    model="gemini-2.0-flash",
)
```

### ClaudeTranslator

```python
from deep_translator import ClaudeTranslator

# Set env var: export ANTHROPIC_API_KEY="your-key"
translator = ClaudeTranslator(source="en", target="german")
result = translator.translate("Hello world")

# Or pass key directly
translator = ClaudeTranslator(
    api_key="your-key",
    source="auto",
    target="spanish",
    model="claude-sonnet-4-20250514",
)
```

### ChatGptTranslator (Updated)

```python
from deep_translator import ChatGptTranslator

# Set env var: export OPEN_API_KEY="your-key"
translator = ChatGptTranslator(source="en", target="korean", model="gpt-4o-mini")
result = translator.translate("Hello world")
```

### GoogleTranslator (No API Key)

```python
from deep_translator import GoogleTranslator

translated = GoogleTranslator(source="auto", target="de").translate("Hello")
```

---

## Use as Middleware (FastAPI / CMS)

This package is designed to work as middleware — called directly from Python code, not via API endpoints. The consuming application handles its own web interface.

```python
from deep_translator import EunoiaTranslator

# Initialize once at startup
_translators: dict = {}

def get_translator(target_lang: str) -> EunoiaTranslator:
    """Get or create a cached translator for the target language."""
    if target_lang not in _translators:
        _translators[target_lang] = EunoiaTranslator(
            source="en",
            target=target_lang,
            quantization="int8",
            model_cache_dir="/app/.ai_models",
        )
    return _translators[target_lang]

def translate_for_user(text: str, user_lang: str) -> str:
    """Translate text before sending to the user's browser."""
    if user_lang == "en":
        return text
    return get_translator(user_lang).translate(text)

# In your FastAPI route or service:
response_text = translate_for_user(ai_response, user_language)
```

---

## CLI

```bash
# Google (default)
dt --translator google --source en --target de --text "Hello world"

# Eunoia (ONNX offline)
dt --translator eunoia --source en --target de --text "Hello world"
dt --translator eunoia --source en --target fr --text "Bonjour" --quantization int4
dt --translator eunoia --source en --target es --text "Hola" --model-cache-dir ./models

# AI translators
dt --translator gemini --source en --target ja --text "Hello"
dt --translator claude --source en --target ko --text "Hello"
dt --translator chatgpt --source en --target ar --text "Hello"

# List supported languages for any translator
dt --translator eunoia --languages
dt --translator google --languages
```

---

## Supported Languages (EunoiaTranslator)

60+ languages via Helsinki-NLP OPUS-MT models:

Afrikaans, Arabic, Azerbaijani, Bengali, Bulgarian, Catalan, Chinese, Czech, Danish, Dutch, English, Esperanto, Estonian, Finnish, French, Galician, German, Greek, Hebrew, Hindi, Hungarian, Icelandic, Indonesian, Irish, Italian, Japanese, Kazakh, Korean, Latvian, Lithuanian, Macedonian, Malay, Maltese, Marathi, Mongolian, Nepali, Norwegian, Persian, Polish, Portuguese, Romanian, Russian, Serbian, Sinhala, Slovak, Slovenian, Spanish, Swahili, Swedish, Tagalog, Tamil, Telugu, Thai, Turkish, Ukrainian, Urdu, Vietnamese, Welsh

Multi-target language groups (ROMANCE, CELTIC, SLAVIC, GERMANIC, CJK, etc.) are used automatically when direct pair models aren't available.

---

## Environment Variables

| Variable | Translator | Required |
|----------|-----------|----------|
| `OPEN_API_KEY` | ChatGptTranslator | Yes |
| `GEMINI_API_KEY` | GeminiTranslator | Yes |
| `ANTHROPIC_API_KEY` | ClaudeTranslator | Yes |
| `DEEPL_API_KEY` | DeeplTranslator | Yes |
| `MICROSOFT_API_KEY` | MicrosoftTranslator | Yes |
| `YANDEX_API_KEY` | YandexTranslator | Yes |
| `LIBRE_API_KEY` | LibreTranslator | Optional |
| `QCRI_API_KEY` | QcriTranslator | Yes |
| `TENCENT_SECRET_ID` | TencentTranslator | Yes |
| `TENCENT_SECRET_KEY` | TencentTranslator | Yes |
| `BAIDU_APPID` | BaiduTranslator | Yes |
| `BAIDU_APPKEY` | BaiduTranslator | Yes |

EunoiaTranslator requires **no environment variables or API keys**.

---

## Development

```bash
# Clone
git clone https://github.com/nidhaloff/deep-translator.git
cd deep-translator

# Install with dev dependencies
poetry install --with dev --extras "ai onnx"

# Run tests
pytest tests/ -v

# Format
black deep_translator/ tests/
isort deep_translator/ tests/
```

---

## What Changed From Upstream

This fork adds the following to the original [deep-translator](https://github.com/nidhaloff/deep-translator):

- **EunoiaTranslator** — offline ONNX-powered translation via Helsinki-NLP OPUS-MT with INT8/INT4 quantization, automatic model downloading, local caching, and English pivot for unsupported direct pairs
- **GeminiTranslator** — Google Gemini API integration
- **ClaudeTranslator** — Anthropic Claude API integration
- **ChatGptTranslator updated** — migrated from deprecated `openai.ChatCompletion` to new OpenAI SDK v1.0+ (`client.chat.completions.create`)
- **Python 3.12+** — minimum version bumped from 3.7
- **New extras** — `[ai]` now bundles OpenAI + Gemini + Claude; `[onnx]` for local inference
- **Dev dependencies** — all bumped to Python 3.12-compatible versions

---

## License

MIT — see [LICENSE](LICENSE) for details.

Original project by [Nidhal Baccouri](https://github.com/nidhaloff).
