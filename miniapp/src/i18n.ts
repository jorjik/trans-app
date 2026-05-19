/** Интернационализация Mini App. */

export const LOCALES: Record<string, Record<string, string>> = {
  ru: {
    /* App */
    'app.loading': 'Initializing TransApp...',
    'app.error.title': 'TransApp Mini App',
    'app.auth_failed': 'Authorization failed.',
    'app.init_error': 'Failed to initialize app.',
    'app.save_error': 'Failed to save settings.',
    'app.chat_create_error': 'Failed to create chat.',
    'app.chat_update_error': 'Failed to update chat.',
    'app.chat_delete_error': 'Failed to delete chat.',
    'app.payment_failed': 'Payment failed. Please try again.',
    'app.checkout_error': 'Failed to create checkout.',
    /* Nav */
    'nav.dashboard': 'Dashboard',
    'nav.chats': 'Chats',
    'nav.billing': 'Billing',
    'nav.settings': 'Settings',
    /* Navbar */
    'nav.plan_remaining': 'Plan: {plan} · Remaining: {chars}',
    /* Dashboard */
    'dashboard.title': 'Dashboard',
    'dashboard.desc': 'Overview of your translation quota and activity.',
    'dashboard.plan': 'Plan',
    'dashboard.remaining': 'Remaining',
    'dashboard.default_lang': 'Default language',
    'dashboard.totals': 'Totals',
    'dashboard.requests': 'Requests: {n}',
    'dashboard.chars': 'Chars: {n}',
    /* Billing */
    'billing.title': 'Billing',
    'billing.desc': 'Upgrade your monthly quota with Telegram Stars.',
    'billing.chars_month': '{n} chars / month',
    'billing.stars': '{n} Stars',
    'billing.current_plan': 'Current plan',
    'billing.pay_stars': 'Pay with Stars',
    /* Chats */
    'chats.title': 'Chats',
    'chats.desc': 'Manage auto-translation rules for Telegram chats.',
    'chats.username_label': 'Chat username',
    'chats.username_placeholder': 'devs_world',
    'chats.source': 'Source',
    'chats.target': 'Target',
    'chats.limit_reached': 'Chat limit reached for your plan.',
    'chats.can_add': 'You can add a new auto-translation chat.',
    'chats.add_btn': 'Add chat',
    'chats.table_chat': 'Chat',
    'chats.table_langs': 'Languages',
    'chats.table_status': 'Status',
    'chats.empty': 'No auto-translate chats yet. Add one above (public username without @).',
    /* Settings */
    'settings.title': 'Settings',
    'settings.desc': 'Configure your default translation preferences.',
    'settings.target_lang': 'Target language',
    'settings.favorite_langs': 'Favorite languages',
    'settings.engine': 'Translation engine',
    'settings.engine_auto': 'Auto',
    'settings.engine_google': 'Google Free',
    'settings.engine_deepl': 'DeepL',
    'settings.save_btn': 'Save changes',
    'settings.ui_language': 'Interface language',
    'settings.ui_lang_ru': 'Русский',
    'settings.ui_lang_en': 'English',
    /* QuickTranslate */
    'qt.title': 'Quick translate',
    'qt.desc': 'Calls the same API as the bot. Cached hits do not spend quota.',
    'qt.text_label': 'Text',
    'qt.text_placeholder': 'Type something to translate...',
    'qt.source': 'Source',
    'qt.target': 'Target',
    'qt.engine': 'Engine',
    'qt.translate_btn': 'Translate',
    'qt.chars_left': '{n} chars left',
    'qt.from_cache': 'From cache · ',
    'qt.failed': 'Translation failed.',
    'qt.result': 'Result',
    'qt.provider': '{provider} · detected {lang}',
    /* QuotaBar */
    'quota.title': 'Monthly quota',
    'quota.used': '{used} / {limit} chars used',
    /* StatsChart */
    'stats.chars': 'Character usage',
    /* LangPicker */
    'lang.not_found': 'No languages found',
  },
  en: {
    /* App */
    'app.loading': 'Initializing TransApp...',
    'app.error.title': 'TransApp Mini App',
    'app.auth_failed': 'Authorization failed.',
    'app.init_error': 'Failed to initialize app.',
    'app.save_error': 'Failed to save settings.',
    'app.chat_create_error': 'Failed to create chat.',
    'app.chat_update_error': 'Failed to update chat.',
    'app.chat_delete_error': 'Failed to delete chat.',
    'app.payment_failed': 'Payment failed. Please try again.',
    'app.checkout_error': 'Failed to create checkout.',
    /* Nav */
    'nav.dashboard': 'Dashboard',
    'nav.chats': 'Chats',
    'nav.billing': 'Billing',
    'nav.settings': 'Settings',
    /* Navbar */
    'nav.plan_remaining': 'Plan: {plan} · Remaining: {chars}',
    /* Dashboard */
    'dashboard.title': 'Dashboard',
    'dashboard.desc': 'Overview of your translation quota and activity.',
    'dashboard.plan': 'Plan',
    'dashboard.remaining': 'Remaining',
    'dashboard.default_lang': 'Default language',
    'dashboard.totals': 'Totals',
    'dashboard.requests': 'Requests: {n}',
    'dashboard.chars': 'Chars: {n}',
    /* Billing */
    'billing.title': 'Billing',
    'billing.desc': 'Upgrade your monthly quota with Telegram Stars.',
    'billing.chars_month': '{n} chars / month',
    'billing.stars': '{n} Stars',
    'billing.current_plan': 'Current plan',
    'billing.pay_stars': 'Pay with Stars',
    /* Chats */
    'chats.title': 'Chats',
    'chats.desc': 'Manage auto-translation rules for Telegram chats.',
    'chats.username_label': 'Chat username',
    'chats.username_placeholder': 'devs_world',
    'chats.source': 'Source',
    'chats.target': 'Target',
    'chats.limit_reached': 'Chat limit reached for your plan.',
    'chats.can_add': 'You can add a new auto-translation chat.',
    'chats.add_btn': 'Add chat',
    'chats.table_chat': 'Chat',
    'chats.table_langs': 'Languages',
    'chats.table_status': 'Status',
    'chats.empty': 'No auto-translate chats yet. Add one above (public username without @).',
    /* Settings */
    'settings.title': 'Settings',
    'settings.desc': 'Configure your default translation preferences.',
    'settings.target_lang': 'Target language',
    'settings.favorite_langs': 'Favorite languages',
    'settings.engine': 'Translation engine',
    'settings.engine_auto': 'Auto',
    'settings.engine_google': 'Google Free',
    'settings.engine_deepl': 'DeepL',
    'settings.save_btn': 'Save changes',
    'settings.ui_language': 'Interface language',
    'settings.ui_lang_ru': 'Русский',
    'settings.ui_lang_en': 'English',
    /* QuickTranslate */
    'qt.title': 'Quick translate',
    'qt.desc': 'Calls the same API as the bot. Cached hits do not spend quota.',
    'qt.text_label': 'Text',
    'qt.text_placeholder': 'Type something to translate...',
    'qt.source': 'Source',
    'qt.target': 'Target',
    'qt.engine': 'Engine',
    'qt.translate_btn': 'Translate',
    'qt.chars_left': '{n} chars left',
    'qt.from_cache': 'From cache · ',
    'qt.failed': 'Translation failed.',
    'qt.result': 'Result',
    'qt.provider': '{provider} · detected {lang}',
    /* QuotaBar */
    'quota.title': 'Monthly quota',
    'quota.used': '{used} / {limit} chars used',
    /* StatsChart */
    'stats.chars': 'Character usage',
    /* LangPicker */
    'lang.not_found': 'No languages found',
  },
};

/** Функция перевода — возвращает текст по ключу и языку. */
export function t(key: string, lang: string = 'en', params?: Record<string, string | number>): string {
  const locale = LOCALES[lang] ?? LOCALES['en'];
  let text = locale[key] ?? LOCALES['en'][key];
  if (!text) {
    console.warn(`Missing i18n key: ${key} (lang=${lang})`);
    return `{${key}}`;
  }
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      text = text.replace(`{${k}}`, String(v));
    }
  }
  return text;
}
