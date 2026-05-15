"""Языковые коды, алиасы, флаги и определение языка."""

from __future__ import annotations

from langdetect import LangDetectException, detect

# Канонические коды (lowercase) → отображаемое имя
LANG_NAMES: dict[str, str] = {
    "en": "English",
    "ru": "Русский",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
    "it": "Italiano",
    "pt": "Português",
    "pl": "Polski",
    "uk": "Українська",
    "tr": "Türkçe",
    "ar": "العربية",
    "zh-cn": "中文 (简体)",
    "zh-tw": "中文 (繁體)",
    "ja": "日本語",
    "ko": "한국어",
    "nl": "Nederlands",
    "sv": "Svenska",
    "cs": "Čeština",
    "da": "Dansk",
    "fi": "Suomi",
    "el": "Ελληνικά",
    "he": "עברית",
    "hi": "हिन्दी",
    "id": "Indonesia",
    "no": "Norsk",
    "ro": "Română",
    "sk": "Slovenský",
    "th": "ไทย",
    "vi": "Tiếng Việt",
    "hu": "Magyar",
    "bg": "Български",
    "hr": "Hrvatski",
    "sr": "Српски",
    "sl": "Slovenščina",
    "et": "Eesti",
    "lv": "Latviešu",
    "lt": "Lietuvių",
    "fa": "فارسی",
    "bn": "বাংলা",
    "ta": "தமிழ்",
    "te": "తెలుగు",
    "ms": "Bahasa Melayu",
    "sw": "Kiswahili",
    "af": "Afrikaans",
    "ca": "Català",
    "eu": "Euskara",
    "gl": "Galego",
    "is": "Íslenska",
    "ga": "Gaeilge",
    "cy": "Cymraeg",
    "sq": "Shqip",
    "hy": "Հայերեն",
    "ka": "ქართული",
    "az": "Azərbaycan",
    "kk": "Қазақ",
    "uz": "Oʻzbek",
    "mn": "Монгол",
    "my": "မြန်မာ",
    "km": "ខ្មែរ",
    "lo": "ລາວ",
    "ne": "नेपाली",
    "si": "සිංහල",
    "am": "አማርኛ",
    "zu": "isiZulu",
}

LANG_FLAGS: dict[str, str] = {
    "en": "🇬🇧",
    "ru": "🇷🇺",
    "de": "🇩🇪",
    "fr": "🇫🇷",
    "es": "🇪🇸",
    "it": "🇮🇹",
    "pt": "🇵🇹",
    "pl": "🇵🇱",
    "uk": "🇺🇦",
    "tr": "🇹🇷",
    "ar": "🇸🇦",
    "zh-cn": "🇨🇳",
    "zh-tw": "🇹🇼",
    "ja": "🇯🇵",
    "ko": "🇰🇷",
    "nl": "🇳🇱",
    "sv": "🇸🇪",
    "cs": "🇨🇿",
    "da": "🇩🇰",
    "fi": "🇫🇮",
    "el": "🇬🇷",
    "he": "🇮🇱",
    "hi": "🇮🇳",
    "id": "🇮🇩",
    "no": "🇳🇴",
    "ro": "🇷🇴",
    "sk": "🇸🇰",
    "th": "🇹🇭",
    "vi": "🇻🇳",
    "hu": "🇭🇺",
    "bg": "🇧🇬",
    "hr": "🇭🇷",
    "sr": "🇷🇸",
    "sl": "🇸🇮",
    "et": "🇪🇪",
    "lv": "🇱🇻",
    "lt": "🇱🇹",
    "fa": "🇮🇷",
    "bn": "🇧🇩",
    "ta": "🇮🇳",
    "te": "🇮🇳",
    "ms": "🇲🇾",
    "sw": "🇰🇪",
    "af": "🇿🇦",
    "ca": "🇪🇸",
    "eu": "🇪🇸",
    "gl": "🇪🇸",
    "is": "🇮🇸",
    "ga": "🇮🇪",
    "cy": "🇬🇧",
    "sq": "🇦🇱",
    "hy": "🇦🇲",
    "ka": "🇬🇪",
    "az": "🇦🇿",
    "kk": "🇰🇿",
    "uz": "🇺🇿",
    "mn": "🇲🇳",
    "my": "🇲🇲",
    "km": "🇰🇭",
    "lo": "🇱🇦",
    "ne": "🇳🇵",
    "si": "🇱🇰",
    "am": "🇪🇹",
    "zu": "🇿🇦",
}

# Алиасы → канонический код
_ALIASES: dict[str, str] = {
    "eng": "en",
    "english": "en",
    "англ": "en",
    "английский": "en",
    "rus": "ru",
    "russian": "ru",
    "рус": "ru",
    "русский": "ru",
    "deu": "de",
    "ger": "de",
    "german": "de",
    "нем": "de",
    "немецкий": "de",
    "fra": "fr",
    "fre": "fr",
    "french": "fr",
    "фр": "fr",
    "французский": "fr",
    "spa": "es",
    "spanish": "es",
    "исп": "es",
    "испанский": "es",
    "ita": "it",
    "italian": "it",
    "ит": "it",
    "итальянский": "it",
    "por": "pt",
    "portuguese": "pt",
    "пор": "pt",
    "pol": "pl",
    "polish": "pl",
    "польский": "pl",
    "ukr": "uk",
    "ukrainian": "uk",
    "укр": "uk",
    "украинский": "uk",
    "tur": "tr",
    "turkish": "tr",
    "турецкий": "tr",
    "ara": "ar",
    "arabic": "ar",
    "арабский": "ar",
    "zh": "zh-cn",
    "cn": "zh-cn",
    "chinese": "zh-cn",
    "mandarin": "zh-cn",
    "китайский": "zh-cn",
    "zho": "zh-cn",
    "jpn": "ja",
    "japanese": "ja",
    "японский": "ja",
    "kor": "ko",
    "korean": "ko",
    "корейский": "ko",
    "nld": "nl",
    "dut": "nl",
    "dutch": "nl",
    "swe": "sv",
    "swedish": "sv",
    "ces": "cs",
    "czech": "cs",
    "dan": "da",
    "danish": "da",
    "fin": "fi",
    "finnish": "fi",
    "ell": "el",
    "gre": "el",
    "greek": "el",
    "heb": "he",
    "hebrew": "he",
    "hin": "hi",
    "hindi": "hi",
    "ind": "id",
    "indonesian": "id",
    "nor": "no",
    "norwegian": "no",
    "ron": "ro",
    "rum": "ro",
    "romanian": "ro",
    "slk": "sk",
    "slovak": "sk",
    "tha": "th",
    "thai": "th",
    "vie": "vi",
    "vietnamese": "vi",
    "zh-cn": "zh-cn",
    "zh-tw": "zh-tw",
    "zh-hans": "zh-cn",
    "zh-hant": "zh-tw",
}

# Канонический код → код для deep-translator / Google
_GOOGLE_CODES: dict[str, str] = {
    "zh-cn": "zh-CN",
    "zh-tw": "zh-TW",
    "he": "iw",
}


def _normalize(code: str) -> str:
    return code.strip().lower().replace("_", "-")


def resolve_lang(code: str) -> str | None:
    """Разрешает пользовательский ввод в канонический ISO-код или None."""
    if not code or not code.strip():
        return None

    normalized = _normalize(code)

    if normalized in LANG_NAMES:
        return normalized

    if normalized in _ALIASES:
        return _ALIASES[normalized]

    # Прямой ISO-код в верхнем регистре (EN → en)
    lower = normalized.lower()
    if lower in LANG_NAMES:
        return lower

    return None


def to_google_lang(code: str) -> str:
    """Код для deep-translator GoogleTranslator."""
    canonical = resolve_lang(code) or _normalize(code)
    return _GOOGLE_CODES.get(canonical, canonical)


def get_lang_name(code: str) -> str:
    canonical = resolve_lang(code) or _normalize(code)
    return LANG_NAMES.get(canonical, canonical.upper())


def get_lang_flag(code: str) -> str:
    canonical = resolve_lang(code) or _normalize(code)
    return LANG_FLAGS.get(canonical, "🌐")


def get_lang_label(code: str) -> str:
    return f"{get_lang_flag(code)} {get_lang_name(code)}"


def detect_language(text: str) -> str | None:
    """Определяет язык текста (канонический код) или None."""
    if not text or not text.strip():
        return None

    try:
        detected = detect(text)
    except LangDetectException:
        return None

    return resolve_lang(detected) or _normalize(detected)
