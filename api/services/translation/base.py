"""Абстрактный базовый класс провайдера перевода."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TranslationResult:
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    provider: str
    cached: bool = False
    char_count: int = 0

    def __post_init__(self):
        if not self.char_count:
            self.char_count = len(self.original_text)


class BaseTranslationProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "auto",
    ) -> TranslationResult:
        """Переводит текст. Выбрасывает исключение при ошибке."""
        ...

    @abstractmethod
    def supports_language(self, lang_code: str) -> bool:
        """Проверяет поддержку языка."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Доступен ли провайдер (есть API ключ и т.д.)."""
        ...
