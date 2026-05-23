"""Клавиатуры и кнопки бота — с локализацией."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from utils.languages import get_lang_flag, get_lang_name
from utils.i18n import t
from config import settings


def main_menu_reply_kb(mini_app_url: str | None = None, ui_lang: str = "ru") -> ReplyKeyboardMarkup:
    """Главное меню в нижней клавиатуре Telegram (reply keyboard)."""
    builder = ReplyKeyboardBuilder()

    if mini_app_url:
        builder.button(
            text=t("btn_open_mini_app", ui_lang),
            web_app=WebAppInfo(url=mini_app_url),
        )

    builder.button(text=t("btn_how_to_use", ui_lang))
    builder.button(text=t("btn_change_lang", ui_lang))
    builder.button(text=t("btn_my_balance", ui_lang))

    # 2 кнопки в ряду: Mini App (если есть) + 3 остальные в 2 ряда
    if mini_app_url:
        builder.adjust(1, 2, 1)
    else:
        builder.adjust(2, 1)

    return builder.as_markup(resize_keyboard=True)


def main_menu_kb(mini_app_url: str | None = None, ui_lang: str = "ru") -> InlineKeyboardMarkup:
    """Главное меню как inline-клавиатура (запасной вариант)."""
    builder = InlineKeyboardBuilder()

    if mini_app_url:
        builder.button(
            text=t("btn_open_mini_app", ui_lang),
            web_app={"url": mini_app_url},
        )
        builder.adjust(1)

    builder.button(text=t("btn_how_to_use", ui_lang), callback_data="help")
    builder.button(text=t("btn_change_lang", ui_lang), callback_data="change_lang")
    builder.button(text=t("btn_my_balance", ui_lang), callback_data="quota")
    builder.adjust(1)

    return builder.as_markup()


def change_lang_kb(favorite_langs: list[str], ui_lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура выбора языка из избранных + популярные."""
    builder = InlineKeyboardBuilder()

    # Избранные языки пользователя
    for code in favorite_langs[:5]:
        flag = get_lang_flag(code)
        name = get_lang_name(code)
        builder.button(text=f"{flag} {name}", callback_data=f"setlang:{code}")

    # Добавляем кнопки управления
    builder.button(text=t("btn_other_lang", ui_lang), callback_data="search_lang")
    builder.button(text=t("btn_back", ui_lang), callback_data="back_main")

    # Сетка: по 2 в ряд для языков и по 1 для нижних кнопок
    sizes = [2] * (len(favorite_langs) // 2)
    if len(favorite_langs) % 2:
        sizes.append(1)
    sizes.extend([1, 1])
    builder.adjust(*sizes)

    return builder.as_markup()


def upgrade_kb(ui_lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопки под балансом (апгрейд + назад)."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_upgrade_starter", ui_lang), callback_data="upgrade:starter")
    builder.button(text=t("btn_invite_friend", ui_lang), callback_data="referral")
    builder.button(text=t("btn_back", ui_lang), callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()


def back_main_kb(ui_lang: str = "ru") -> InlineKeyboardMarkup:
    """Простая кнопка Назад в главное меню."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_back", ui_lang), callback_data="back_main")
    return builder.as_markup()


def translate_result_kb(
    source_lang: str,
    target_lang: str,
    original_text: str,
    ui_lang: str = "ru",
) -> InlineKeyboardMarkup:
    """Кнопки под результатом перевода."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_other_target", ui_lang), callback_data=f"retranslate:{source_lang}")
    builder.button(text=t("btn_done", ui_lang), callback_data="dismiss")
    builder.adjust(2)
    return builder.as_markup()


def popular_langs_kb(ui_lang: str = "ru", callback_prefix: str = "setlang") -> InlineKeyboardMarkup:
    """Список популярных языков для быстрого выбора."""
    top = ["en", "ru", "de", "fr", "es", "it", "pt", "pl", "uk", "tr",
           "ar", "zh-cn", "ja", "ko", "nl", "sv"]
    builder = InlineKeyboardBuilder()
    for code in top:
        flag = get_lang_flag(code)
        name = get_lang_name(code)
        builder.button(text=f"{flag} {name}", callback_data=f"{callback_prefix}:{code}")
    builder.button(text=t("btn_back", ui_lang), callback_data="change_lang")
    builder.adjust(3, 3, 3, 3, 3, 1, 1)
    return builder.as_markup()


def ui_lang_kb(current_ui_lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура выбора языка интерфейса (EN / RU / UK)."""
    builder = InlineKeyboardBuilder()
    for code, flag, name in [
        ("en", "🇬🇧", "English"),
        ("ru", "🌐", "Русский"),
        ("uk", "🇺🇦", "Українська"),
    ]:
        label = f"✅ {flag} {name}" if current_ui_lang == code else f"{flag} {name}"
        builder.button(text=label, callback_data=f"set_ui_lang:{code}")
    builder.adjust(1)
    return builder.as_markup()
