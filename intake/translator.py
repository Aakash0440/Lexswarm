# intake/translator.py
# Multilingual translation — converts any language to English for processing
# Uses Helsinki-NLP models (free, runs locally, no API key)
# Supports 100+ languages via opus-mt model family

from dataclasses import dataclass


@dataclass
class TranslationResult:
    original_text: str
    translated_text: str
    source_language: str
    target_language: str = "en"
    confidence: float = 1.0
    used_fallback: bool = False


class MultilingualTranslator:
    """
    Translates legal case descriptions to English for processing.
    Uses Helsinki-NLP/opus-mt models — free, local, no API key needed.

    Supported language pairs (examples):
      ur -> en  (Urdu)
      id -> en  (Indonesian / Bahasa)
      ar -> en  (Arabic)
      hi -> en  (Hindi)
      fr -> en  (French)
      sw -> en  (Swahili)
      bn -> en  (Bengali)
      tl -> en  (Filipino/Tagalog)

    Falls back to original text if language is already English
    or if translation model unavailable.
    """

    # Helsinki-NLP model names per source language
    OPUS_MT_MODELS = {
        "ur": "Helsinki-NLP/opus-mt-ur-en",
        "id": "Helsinki-NLP/opus-mt-id-en",
        "ar": "Helsinki-NLP/opus-mt-ar-en",
        "hi": "Helsinki-NLP/opus-mt-hi-en",
        "fr": "Helsinki-NLP/opus-mt-fr-en",
        "es": "Helsinki-NLP/opus-mt-es-en",
        "sw": "Helsinki-NLP/opus-mt-sw-en",
        "bn": "Helsinki-NLP/opus-mt-bn-en",
        "tl": "Helsinki-NLP/opus-mt-tl-en",
        "zh": "Helsinki-NLP/opus-mt-zh-en",
        "pt": "Helsinki-NLP/opus-mt-pt-en",
        "ru": "Helsinki-NLP/opus-mt-ru-en",
        "de": "Helsinki-NLP/opus-mt-de-en",
        "tr": "Helsinki-NLP/opus-mt-tr-en",
        "fa": "Helsinki-NLP/opus-mt-fa-en",
    }

    def __init__(self):
        self._pipelines: dict = {}   # cache loaded models

    def _get_pipeline(self, source_lang: str):
        """Lazy load translation pipeline for a given language."""
        if source_lang not in self._pipelines:
            model_name = self.OPUS_MT_MODELS.get(source_lang)
            if not model_name:
                return None
            try:
                from transformers import pipeline
                self._pipelines[source_lang] = pipeline(
                    "translation",
                    model=model_name,
                    max_length=512,
                )
                print(f"[Translator] Loaded {model_name}")
            except Exception as e:
                print(f"[Translator] Failed to load {model_name}: {e}")
                return None
        return self._pipelines.get(source_lang)

    def translate(self, text: str, source_lang: str) -> TranslationResult:
        """Translate text from source_lang to English."""
        if source_lang == "en":
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language="en",
                confidence=1.0,
            )

        pipe = self._get_pipeline(source_lang)
        if pipe is None:
            print(f"[Translator] No model for {source_lang} — using original text")
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_lang,
                used_fallback=True,
                confidence=0.5,
            )

        try:
            result = pipe(text[:500])[0]
            translated = result.get("translation_text", text)
            return TranslationResult(
                original_text=text,
                translated_text=translated,
                source_language=source_lang,
                confidence=0.85,
            )
        except Exception as e:
            print(f"[Translator] Translation failed: {e}")
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_lang,
                used_fallback=True,
                confidence=0.3,
            )

    def translate_to_user_language(self, english_text: str, target_lang: str) -> str:
        """
        Translate English output back to user's language.
        Used for final response generation.
        """
        if target_lang == "en":
            return english_text

        # Reverse models
        reverse_models = {
            "ur": "Helsinki-NLP/opus-mt-en-ur",
            "id": "Helsinki-NLP/opus-mt-en-id",
            "ar": "Helsinki-NLP/opus-mt-en-ar",
            "hi": "Helsinki-NLP/opus-mt-en-hi",
            "fr": "Helsinki-NLP/opus-mt-en-fr",
            "es": "Helsinki-NLP/opus-mt-en-es",
            "sw": "Helsinki-NLP/opus-mt-en-sw",
        }

        model_name = reverse_models.get(target_lang)
        if not model_name:
            return english_text

        cache_key = f"en_{target_lang}"
        if cache_key not in self._pipelines:
            try:
                from transformers import pipeline
                self._pipelines[cache_key] = pipeline("translation", model=model_name, max_length=512)
            except Exception:
                return english_text

        try:
            result = self._pipelines[cache_key](english_text[:500])[0]
            return result.get("translation_text", english_text)
        except Exception:
            return english_text
