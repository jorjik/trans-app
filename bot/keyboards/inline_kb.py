"""Inline-клавиатуры и кнопки бота."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.languages import get_lang_flag, get_lang_name, LANG_FLAGS
from config import settings


def main_menu_kb(mini_app_url: str | None = None) -> InlineKeyboardMarkup:
    """Главное меню в /start."""
    builder = InlineKeyboardBuilder()

    if mini_app_url:
        builder.button(
            text="⚙️ Открыть Mini App",
            web_app={"url": mini_app_url},
        )
        builder.adjust(1)

    builder.button(text="📖 Как пользоваться", callback_data="help")
    builder.button(text="🌍 Изменить язык", callback_data="change_lang")
    builder.button(text="📊 Мой баланс", callback_data="quota")
    builder.adjust(1)

    return builder.as_markup()


def change_lang_kb(favorite_langs: list[str]) -> InlineKeyboardMarkup:
    """Клавиатура выбора языка из избранных + популярные."""
    builder = InlineKeyboardBuilder()

    # Избранные языки пользователя
    for code in favorite_langs[:5]:
        flag = get_lang_flag(code)
        name = get_lang_name(code)
        builder.button(text=f"{flag} {name}", callback_data=f"setlang:{code}")

    builder.adjust(2)

    # Кнопка "другой язык"
    builder.button(text="🔍 Другой язык...", callback_data="search_lang")
    builder.button(text="◀️ Назад", callback_data="back_main")
    builder.adjust(1, last=True)

    return builder.as_markup()


def upgrade_kb() -> InlineKeyboardMarkup:
    """Кнопки при превышении квоты."""
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Starter — 250 Stars/мес", callback_data="upgrade:starter")
    builder.button(text="👥 Пригласить друга (+10k символов)", callback_data="referral")
    builder.button(text="❓ Подробнее о планах", callback_data="plans")
    builder.adjust(1)
    return builder.as_markup()


def translate_result_kb(
    source_lang: str,
    target_lang: str,
    original_text: str,
) -> InlineKeyboardMarkup:
    """Кнопки под результатом перевода."""
    builder = InlineKeyboardBuilder()

    # Перевести на другой язык
    builder.button(text="🔄 Другой язык", callback_data=f"retranslate:{source_lang}")
    # Копировать (информационная кнопка)
    builder.button(text="✅ Готово", callback_data="dismiss")
    builder.adjust(2)

    return builder.as_markup()


def popular_langs_kb() -> InlineKeyboardMarkup:
    """Список популярных языков для быстрого выбора."""
    top = ["en", "ru", "de", "fr", "es", "it", "pt", "pl", "uk", "tr",
           "ar", "zh-cn", "ja", "ko", "nl", "sv"]
    builder = InlineKeyboardBuilder()
    for code in top:
        flag = get_lang_flag(code)
        name = get_lang_name(code)
        builder.button(text=f"{flag} {name}", callback_data=f"setlang:{code}")
    builder.adjust(3)
    builder.button(text="◀️ Назад", callback_data="change_lang")
    builder.adjust(1, last=True)
    return builder.as_markup()
