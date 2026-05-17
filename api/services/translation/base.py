"""Абстрактный базовый класс для MT-провайдеров."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TranslationResult:
    original_text: str
    translated_text: str
    source_lang: str       # определённый или переданный
    target_lang: str
    provider: str
    cached: bool = False
    char_count: int = 0

    def __post_init__(self):
        if not self.char_count:
            self.char_count = len(self.original_text)


class BaseTranslationProvider(ABC):
    """Интерфейс MT-провайдера."""

    name: str = "base"

    @abstractmethod
    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "auto",
    ) -> TranslationResult:
        """Переводит текст. Выбрасывает RuntimeError при ошибке."""
        ...

    @abstractmethod
    def supports_language(self, lang_code: str) -> bool:
        """Возвращает True если язык поддерживается."""
        ...

    def count_chars(self, text: str) -> int:
        return len(text)
