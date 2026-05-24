"""Generate miniapp locale entries for 7 new languages using deep-translator."""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from deep_translator import GoogleTranslator

# Source English locale keys/values from i18n.ts
EN_LOCALE = {
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
    'nav.dashboard': 'Dashboard',
    'nav.chats': 'Chats',
    'nav.billing': 'Billing',
    'nav.settings': 'Settings',
    'nav.plan_remaining': 'Plan: {plan} · Remaining: {chars}',
    'dashboard.title': 'Dashboard',
    'dashboard.desc': 'Overview of your translation quota and activity.',
    'dashboard.plan': 'Plan',
    'dashboard.remaining': 'Remaining',
    'dashboard.default_lang': 'Default language',
    'dashboard.totals': 'Totals',
    'dashboard.requests': 'Requests: {n}',
    'dashboard.chars': 'Chars: {n}',
    'billing.title': 'Billing',
    'billing.desc': 'Upgrade your monthly quota with Telegram Stars.',
    'billing.chars_month': '{n} chars / month',
    'billing.stars': '{n} Stars',
    'billing.current_plan': 'Current plan',
    'billing.pay_stars': 'Pay with Stars',
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
    'settings.ui_lang_uk': 'Українська',
    'qt.title': 'Quick translate',
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
    'qt.copy': 'Copy',
    'qt.copied': 'Copied!',
    'quota.title': 'Monthly quota',
    'quota.used': '{used} / {limit} chars used',
    'stats.chars': 'Character usage',
    'lang.not_found': 'No languages found',
    'langpicker.title': 'Welcome! Choose your language',
    'langpicker.desc': 'Select your interface language. You can change it later in Settings.',
    'langpicker.en': 'English',
    'langpicker.ru': 'Русский',
    'langpicker.uk': 'Українська',
    'langpicker.continue': 'Continue',
}

# Language names localized (for LANG_NAMES_LOCALIZED)
EN_LANG_NAMES = {
    'auto': 'Auto detect',
    'en': 'English',
    'ru': 'Russian',
    'uk': 'Ukrainian',
    'de': 'German',
    'fr': 'French',
    'es': 'Spanish',
    'it': 'Italian',
    'pl': 'Polish',
    'tr': 'Turkish',
    'zh': 'Chinese',
    'ja': 'Japanese',
}

def extract_placeholders(text):
    return re.findall(r'\{([^}]+)\}', text)

def translate_text(text, target_lang):
    try:
        return GoogleTranslator(source='en', target=target_lang).translate(text)
    except Exception as e:
        print(f'  ERROR: {e}')
        return text

def fix_placeholders(translated, original):
    orig_phs = extract_placeholders(original)
    if not orig_phs:
        return translated
    for ph in orig_phs:
        full_ph = '{' + ph + '}'
        if full_ph not in translated:
            translated += ' ' + full_ph
    return translated

# Languages to generate
TARGET_LANGS = ['de', 'fr', 'es', 'it', 'pt', 'pl', 'tr']

for lang in TARGET_LANGS:
    print(f'\n=== {lang} ===')
    
    # Translate main locale
    result = {}
    for key, value in EN_LOCALE.items():
        print(f'  {key}')
        if key.startswith('settings.ui_lang_'):
            # These are language names in their native form - keep as-is for en/ru/uk
            # For others, translate the language name
            if key == 'settings.ui_lang_en':
                result[key] = 'English'
            elif key == 'settings.ui_lang_ru':
                result[key] = 'Русский'
            elif key == 'settings.ui_lang_uk':
                result[key] = 'Українська'
            else:
                result[key] = fix_placeholders(translate_text(value, lang), value)
        else:
            translated = translate_text(value, lang)
            result[key] = fix_placeholders(translated, value)
    
    # Translate lang names
    lang_names = {}
    for code, name in EN_LANG_NAMES.items():
        print(f'  lang_name: {code}')
        translated = translate_text(name, lang)
        lang_names[code] = fix_placeholders(translated, name)
    
    # Add 'pt' to lang_names (was missing)
    if 'pt' not in lang_names:
        lang_names['pt'] = fix_placeholders(translate_text('Portuguese', lang), 'Portuguese')
    
    # Output as TypeScript
    print(f'\n  --- LOCALES[{lang}] ---')
    for key in sorted(result.keys()):
        val = result[key].replace('\\', '\\\\').replace("'", "\\'")
        print(f"    '{key}': '{val}',")
    
    print(f'\n  --- LANG_NAMES_LOCALIZED[{lang}] ---')
    for code in sorted(lang_names.keys()):
        val = lang_names[code].replace('\\', '\\\\').replace("'", "\\'")
        print(f"    {code}: '{val}',")
