"""Клавиатуры и кнопки бота — с локализацией."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from utils.languages import get_lang_flag, get_lang_name, UI_LANGUAGES
from utils.i18n import t
from config import settings
from services.billing import BILLABLE_PLANS


def main_menu_reply_kb(ui_lang: str = "ru", user_id: int | None = None) -> ReplyKeyboardMarkup:
    """Главное меню в нижней клавиатуре Telegram (reply keyboard)."""
    builder = ReplyKeyboardBuilder()
    builder.button(text=t("btn_how_to_use", ui_lang))
    builder.button(text=t("btn_change_lang", ui_lang))
    builder.button(text=t("btn_my_balance", ui_lang))
    # Кнопка /admin только для админов
    buttons = 2
    if user_id and user_id in settings.admin_tg_ids:
        builder.button(text="⚙️ Admin")
        buttons = 3
    builder.adjust(buttons, 1)
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
    """Кнопки под балансом (выбор тарифа + назад)."""
    builder = InlineKeyboardBuilder()
    for plan_id in ["starter", "pro", "business"]:
        plan = BILLABLE_PLANS.get(plan_id)
        if plan:
            label = t(f"plan_{plan_id}", ui_lang)
            builder.button(text=f"{label} — {plan.stars} ⭐", callback_data=f"upgrade:{plan_id}")
    builder.button(text=t("btn_invite_friend", ui_lang), callback_data="referral")
    builder.button(text=t("btn_back", ui_lang), callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()


def billing_methods_kb(
    plan_id: str,
    ui_lang: str = "ru",
    visible: dict | None = None,
) -> InlineKeyboardMarkup:
    """Выбор способа оплаты для тарифного плана.
    Параметр visible — словарь вида {"stars": True, "kofi": True, "paypal": True}.
    Если None, показывает всё.
    """
    builder = InlineKeyboardBuilder()
    if visible is None or visible.get("stars", True):
        builder.button(text=t("billing_method_stars", ui_lang), callback_data=f"pay_stars:{plan_id}")
    if visible is None or visible.get("kofi", True):
        builder.button(text=t("billing_method_kofi", ui_lang), callback_data=f"pay_kofi:{plan_id}")
    if visible is None or visible.get("paypal", True):
        builder.button(text=t("billing_method_paypal", ui_lang), callback_data=f"pay_paypal:{plan_id}")
    builder.button(text=t("btn_back", ui_lang), callback_data="quota")
    builder.adjust(1)
    return builder.as_markup()


def kofi_payment_kb(page_url: str, ui_lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопка для оплаты через Ko-fi."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("billing_kofi_open", ui_lang),
        url=page_url,
    )
    builder.button(text=t("btn_back", ui_lang), callback_data="quota")
    builder.adjust(1)
    return builder.as_markup()


def paypal_payment_kb(approval_url: str, order_id: str, ui_lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопки для оплаты через PayPal."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=t("billing_paypal_approve", ui_lang),
        url=approval_url,
    )
    builder.button(
        text=t("billing_paypal_check", ui_lang),
        callback_data=f"paypal_check:{order_id}",
    )
    builder.button(text=t("btn_back", ui_lang), callback_data="quota")
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


def admin_menu_kb(ui_lang: str = "ru") -> InlineKeyboardMarkup:
    """Админ-меню."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t("admin_btn_stats", ui_lang), callback_data="admin_stats")
    builder.button(text=t("admin_btn_payment", ui_lang), callback_data="admin_payment")
    builder.button(text=t("btn_back", ui_lang), callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()


def admin_payment_kb(config: dict, ui_lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура настройки видимости способов оплаты."""
    builder = InlineKeyboardBuilder()
    methods = [
        ("stars", f"⭐ Stars {'✅' if config.get('stars', True) else '❌'}", "admin_toggle:stars"),
        ("kofi", f"☕ Ko-fi {'✅' if config.get('kofi', True) else '❌'}", "admin_toggle:kofi"),
        ("paypal", f"💳 PayPal {'✅' if config.get('paypal', True) else '❌'}", "admin_toggle:paypal"),
    ]
    for _, label, cb in methods:
        builder.button(text=label, callback_data=cb)
    builder.button(text=t("btn_back", ui_lang), callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()


def ui_lang_kb(current_ui_lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура выбора языка интерфейса (10 языков)."""
    builder = InlineKeyboardBuilder()
    for code in UI_LANGUAGES:
        flag = get_lang_flag(code)
        name = get_lang_name(code)
        label = f"✅ {flag} {name}" if current_ui_lang == code else f"{flag} {name}"
        builder.button(text=label, callback_data=f"set_ui_lang:{code}")
    builder.adjust(2)
    return builder.as_markup()
