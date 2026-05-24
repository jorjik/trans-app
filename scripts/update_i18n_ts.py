"""Update miniapp/src/i18n.ts with 7 new language locales."""
import json
import re
import os

# Read the generated locale data from bot locales
LOCALES_DIR = os.path.join(os.path.dirname(__file__), '..', 'bot', 'locales')

# Build locale data from bot JSON files
def build_locale_data():
    """Build the LOCALES dict from bot locale JSON files."""
    # Read en.json to get all keys
    with open(os.path.join(LOCALES_DIR, 'en.json'), encoding='utf-8') as f:
        en = json.load(f)
    
    # Map bot locale keys to miniapp locale keys
    KEY_MAP = {
        # App
        'loading': 'app.loading',
        'mini_app_error_title': 'app.error.title',
        # These are constructed specially
    }
    
    result = {}
    
    # First build from en.json as reference
    for lang in ['de', 'fr', 'es', 'it', 'pt', 'pl', 'tr']:
        filepath = os.path.join(LOCALES_DIR, f'{lang}.json')
        if not os.path.exists(filepath):
            continue
        with open(filepath, encoding='utf-8') as f:
            data = json.load(f)
        
        lang_data = {}
        
        # Map keys from bot locale to miniapp locale
        # Bot keys -> miniapp keys
        key_mapping = {
            'loading': 'app.loading',
            'mini_app_error_title': 'app.error.title',
            # Nav
            'nav_dashboard': 'nav.dashboard',
            'nav_chats': 'nav.chats',
            'nav_billing': 'nav.billing',
            'nav_settings': 'nav.settings',
            # Dashboard
            'dashboard_title': 'dashboard.title',
            'dashboard_desc': 'dashboard.desc',
            'dashboard_plan': 'dashboard.plan',
            'dashboard_remaining': 'dashboard.remaining',
            'dashboard_default_lang': 'dashboard.default_lang',
            'dashboard_totals': 'dashboard.totals',
            'dashboard_requests': 'dashboard.requests',
            'dashboard_chars': 'dashboard.chars',
            # Billing
            'billing_title': 'billing.title',
            'billing_desc': 'billing.desc',
            'billing_chars_month': 'billing.chars_month',
            'billing_stars': 'billing.stars',
            'billing_current_plan': 'billing.current_plan',
            'billing_pay_stars': 'billing.pay_stars',
            # Chats
            'chats_title': 'chats.title',
            'chats_desc': 'chats.desc',
            'chats_username_label': 'chats.username_label',
            'chats_username_placeholder': 'chats.username_placeholder',
            'chats_source': 'chats.source',
            'chats_target': 'chats.target',
            'chats_limit_reached': 'chats.limit_reached',
            'chats_can_add': 'chats.can_add',
            'chats_add_btn': 'chats.add_btn',
            'chats_table_chat': 'chats.table_chat',
            'chats_table_langs': 'chats.table_langs',
            'chats_table_status': 'chats.table_status',
            'chats_empty': 'chats.empty',
            # Settings
            'settings_title': 'settings.title',
            'settings_desc': 'settings.desc',
            'settings_target_lang': 'settings.target_lang',
            'settings_favorite_langs': 'settings.favorite_langs',
            'settings_engine': 'settings.engine',
            'settings_engine_auto': 'settings.engine_auto',
            'settings_engine_google': 'settings.engine_google',
            'settings_engine_deepl': 'settings.engine_deepl',
            'settings_save_btn': 'settings.save_btn',
            'settings_ui_language': 'settings.ui_language',
            # Quick Translate
            'qt_title': 'qt.title',
            'qt_text_label': 'qt.text_label',
            'qt_text_placeholder': 'qt.text_placeholder',
            'qt_source': 'qt.source',
            'qt_target': 'qt.target',
            'qt_engine': 'qt.engine',
            'qt_translate_btn': 'qt.translate_btn',
            'qt_chars_left': 'qt.chars_left',
            'qt_from_cache': 'qt.from_cache',
            'qt_failed': 'qt.failed',
            'qt_result': 'qt.result',
            'qt_provider': 'qt.provider',
            'qt_copy': 'qt.copy',
            'qt_copied': 'qt.copied',
            # Quota
            'quota_title': 'quota.title',
            'quota_used': 'quota.used',
            # Stats
            'stats_chars': 'stats.chars',
            # Lang
            'lang_not_found': 'lang.not_found',
            # LangPicker
            'langpicker_title': 'langpicker.title',
            'langpicker_desc': 'langpicker.desc',
            'langpicker_continue': 'langpicker.continue',
        }
        
        for bot_key, mini_key in key_mapping.items():
            if bot_key in data:
                lang_data[mini_key] = data[bot_key]
        
        # Handle specific keys with special names
        lang_data['app.auth_failed'] = data.get('auth_failed', 'Authorization failed.')
        lang_data['app.init_error'] = data.get('init_error', 'Failed to initialize app.')
        lang_data['app.save_error'] = data.get('save_error', 'Failed to save settings.')
        lang_data['app.chat_create_error'] = data.get('chat_create_error', 'Failed to create chat.')
        lang_data['app.chat_update_error'] = data.get('chat_update_error', 'Failed to update chat.')
        lang_data['app.chat_delete_error'] = data.get('chat_delete_error', 'Failed to delete chat.')
        lang_data['app.payment_failed'] = data.get('payment_failed', 'Payment failed. Please try again.')
        lang_data['app.checkout_error'] = data.get('checkout_error', 'Failed to create checkout.')
        
        # Handle ui_lang_* keys - these stay as native names
        lang_data['settings.ui_lang_ru'] = 'Русский'
        lang_data['settings.ui_lang_en'] = 'English'
        lang_data['settings.ui_lang_uk'] = 'Українська'
        
        # LangPicker lang names - localized to the target language
        lang_data['langpicker.en'] = data.get('langpicker_en', 'English')
        lang_data['langpicker.ru'] = data.get('langpicker_ru', 'Russian')
        lang_data['langpicker.uk'] = data.get('langpicker_uk', 'Ukrainian')
        
        # Handle nav.plan_remaining
        lang_data['nav.plan_remaining'] = data.get('plan_remaining', 'Plan: {plan} · Remaining: {chars}')
        
        result[lang] = lang_data
    
    return result


def generate_i18n_content():
    """Generate the complete i18n.ts content."""
    # Read the current i18n.ts
    i18n_path = os.path.join(os.path.dirname(__file__), '..', 'miniapp', 'src', 'i18n.ts')
    with open(i18n_path, encoding='utf-8') as f:
        content = f.read()
    
    # Get the locale data from the bot JSON files
    locale_data = build_locale_data()
    
    # English locale is the reference
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
    
    # Corrected translations with proper placeholders
    LOCALES = {
        'de': {
            'app.loading': 'TransApp wird initialisiert...',
            'app.error.title': 'TransApp Mini-App',
            'app.auth_failed': 'Die Autorisierung ist fehlgeschlagen.',
            'app.init_error': 'App konnte nicht initialisiert werden.',
            'app.save_error': 'Einstellungen konnten nicht gespeichert werden.',
            'app.chat_create_error': 'Chat konnte nicht erstellt werden.',
            'app.chat_update_error': 'Chat konnte nicht aktualisiert werden.',
            'app.chat_delete_error': 'Der Chat konnte nicht gelöscht werden.',
            'app.payment_failed': 'Die Zahlung ist fehlgeschlagen. Bitte versuchen Sie es erneut.',
            'app.checkout_error': 'Checkout konnte nicht erstellt werden.',
            'nav.dashboard': 'Dashboard',
            'nav.chats': 'Chats',
            'nav.billing': 'Abrechnung',
            'nav.settings': 'Einstellungen',
            'nav.plan_remaining': 'Plan: {plan} · Verbleibend: {chars}',
            'dashboard.title': 'Dashboard',
            'dashboard.desc': 'Überblick über Ihr Übersetzungskontingent und Ihre Übersetzungsaktivität.',
            'dashboard.plan': 'Plan',
            'dashboard.remaining': 'Übrig',
            'dashboard.default_lang': 'Standardsprache',
            'dashboard.totals': 'Gesamt',
            'dashboard.requests': 'Anfragen: {n}',
            'dashboard.chars': 'Zeichen: {n}',
            'billing.title': 'Abrechnung',
            'billing.desc': 'Erweitern Sie Ihr monatliches Kontingent mit Telegram Stars.',
            'billing.chars_month': '{n} Zeichen/Monat',
            'billing.stars': '{n} Sterne',
            'billing.current_plan': 'Aktueller Plan',
            'billing.pay_stars': 'Bezahlen Sie mit Sternen',
            'chats.title': 'Chats',
            'chats.desc': 'Verwalten Sie automatische Übersetzungsregeln für Telegram-Chats.',
            'chats.username_label': 'Chat-Benutzername',
            'chats.username_placeholder': 'devs_world',
            'chats.source': 'Quelle',
            'chats.target': 'Ziel',
            'chats.limit_reached': 'Das Chat-Limit für Ihren Plan wurde erreicht.',
            'chats.can_add': 'Sie können einen neuen Autoübersetzungs-Chat hinzufügen.',
            'chats.add_btn': 'Chat hinzufügen',
            'chats.table_chat': 'Chat',
            'chats.table_langs': 'Sprachen',
            'chats.table_status': 'Status',
            'chats.empty': 'Noch keine automatisch übersetzten Chats. Fügen Sie oben einen hinzu (öffentlicher Benutzername ohne @).',
            'settings.title': 'Einstellungen',
            'settings.desc': 'Konfigurieren Sie Ihre Standardübersetzungseinstellungen.',
            'settings.target_lang': 'Zielsprache',
            'settings.favorite_langs': 'Lieblingssprachen',
            'settings.engine': 'Übersetzungsmaschine',
            'settings.engine_auto': 'Auto',
            'settings.engine_google': 'Google Free',
            'settings.engine_deepl': 'DeepL',
            'settings.save_btn': 'Änderungen speichern',
            'settings.ui_language': 'Schnittstellensprache',
            'settings.ui_lang_ru': 'Русский',
            'settings.ui_lang_en': 'English',
            'settings.ui_lang_uk': 'Українська',
            'qt.title': 'Schnelle Übersetzung',
            'qt.text_label': 'Text',
            'qt.text_placeholder': 'Geben Sie etwas zum Übersetzen ein...',
            'qt.source': 'Quelle',
            'qt.target': 'Ziel',
            'qt.engine': 'Motor',
            'qt.translate_btn': 'Übersetzen',
            'qt.chars_left': '{n} Zeichen übrig',
            'qt.from_cache': 'Aus dem Cache ·',
            'qt.failed': 'Die Übersetzung ist fehlgeschlagen.',
            'qt.result': 'Ergebnis',
            'qt.provider': '{provider} · {lang} erkannt',
            'qt.copy': 'Kopieren',
            'qt.copied': 'Kopiert!',
            'quota.title': 'Monatliches Kontingent',
            'quota.used': '{used} / {limit} Zeichen verwendet',
            'stats.chars': 'Zeichenverwendung',
            'lang.not_found': 'Keine Sprachen gefunden',
            'langpicker.title': 'Willkommen! Wählen Sie Ihre Sprache',
            'langpicker.desc': 'Wählen Sie die Sprache Ihrer Benutzeroberfläche. Sie können es später in den Einstellungen ändern.',
            'langpicker.en': 'Englisch',
            'langpicker.ru': 'Russisch',
            'langpicker.uk': 'Ukrainisch',
            'langpicker.continue': 'Weiter',
        },
        'fr': {
            'app.loading': 'Initialisation de TransApp...',
            'app.error.title': 'Mini-application TransApp',
            'app.auth_failed': "L'autorisation a échoué.",
            'app.init_error': "Échec de l'initialisation de l'application.",
            'app.save_error': "Échec de l'enregistrement des paramètres.",
            'app.chat_create_error': 'Échec de la création du chat.',
            'app.chat_update_error': 'Échec de la mise à jour du chat.',
            'app.chat_delete_error': 'Échec de la suppression du chat.',
            'app.payment_failed': 'Le paiement a échoué. Veuillez réessayer.',
            'app.checkout_error': "Échec de la création du paiement.",
            'nav.dashboard': 'Tableau de bord',
            'nav.chats': 'Discussions',
            'nav.billing': 'Facturation',
            'nav.settings': 'Paramètres',
            'nav.plan_remaining': 'Plan : {plan} · Restant : {chars}',
            'dashboard.title': 'Tableau de bord',
            'dashboard.desc': "Aperçu de votre quota de traduction et de votre activité.",
            'dashboard.plan': 'Plan',
            'dashboard.remaining': 'Restant',
            'dashboard.default_lang': 'Langue par défaut',
            'dashboard.totals': 'Totaux',
            'dashboard.requests': 'Demandes : {n}',
            'dashboard.chars': 'Caractères : {n}',
            'billing.title': 'Facturation',
            'billing.desc': 'Améliorez votre quota mensuel avec Telegram Stars.',
            'billing.chars_month': '{n} caractères/mois',
            'billing.stars': '{n} étoiles',
            'billing.current_plan': 'Forfait actuel',
            'billing.pay_stars': 'Payez avec des étoiles',
            'chats.title': 'Discussions',
            'chats.desc': 'Gérez les règles de traduction automatique pour les discussions Telegram.',
            'chats.username_label': "Nom d'utilisateur du chat",
            'chats.username_placeholder': 'devs_monde',
            'chats.source': 'Source',
            'chats.target': 'Cible',
            'chats.limit_reached': 'Limite de chat atteinte pour votre forfait.',
            'chats.can_add': 'Vous pouvez ajouter un nouveau chat de traduction automatique.',
            'chats.add_btn': 'Ajouter un chat',
            'chats.table_chat': 'Chat',
            'chats.table_langs': 'Langues',
            'chats.table_status': 'Statut',
            'chats.empty': "Pas encore de chats de traduction automatique. Ajoutez-en un ci-dessus (nom d'utilisateur public sans @).",
            'settings.title': 'Paramètres',
            'settings.desc': 'Configurez vos préférences de traduction par défaut.',
            'settings.target_lang': 'Langue cible',
            'settings.favorite_langs': 'Langues préférées',
            'settings.engine': 'Moteur de traduction',
            'settings.engine_auto': 'Auto',
            'settings.engine_google': 'Google Free',
            'settings.engine_deepl': 'DeepL',
            'settings.save_btn': 'Enregistrer les modifications',
            'settings.ui_language': "Langue de l'interface",
            'settings.ui_lang_ru': 'Русский',
            'settings.ui_lang_en': 'English',
            'settings.ui_lang_uk': 'Українська',
            'qt.title': 'Traduction rapide',
            'qt.text_label': 'Texte',
            'qt.text_placeholder': 'Tapez quelque chose à traduire...',
            'qt.source': 'Source',
            'qt.target': 'Cible',
            'qt.engine': 'Moteur',
            'qt.translate_btn': 'Traduire',
            'qt.chars_left': '{n} caractères restants',
            'qt.from_cache': 'Depuis le cache ·',
            'qt.failed': 'La traduction a échoué.',
            'qt.result': 'Résultat',
            'qt.provider': '{provider} · {lang} détecté',
            'qt.copy': 'Copier',
            'qt.copied': 'Copié !',
            'quota.title': 'Quota mensuel',
            'quota.used': '{used} / {limit} caractères utilisés',
            'stats.chars': 'Utilisation des caractères',
            'lang.not_found': 'Aucune langue trouvée',
            'langpicker.title': 'Bienvenue ! Choisissez votre langue',
            'langpicker.desc': "Sélectionnez la langue de votre interface. Vous pourrez la modifier ultérieurement dans Paramètres.",
            'langpicker.en': 'Anglais',
            'langpicker.ru': 'Russe',
            'langpicker.uk': 'Ukrainien',
            'langpicker.continue': 'Continuer',
        },
        'es': {
            'app.loading': 'Inicializando TransApp...',
            'app.error.title': 'TransApp Mini App',
            'app.auth_failed': 'La autorización falló.',
            'app.init_error': 'No se pudo inicializar la aplicación.',
            'app.save_error': 'No se pudo guardar la configuración.',
            'app.chat_create_error': 'No se pudo crear el chat.',
            'app.chat_update_error': 'No se pudo actualizar el chat.',
            'app.chat_delete_error': 'No se pudo eliminar el chat.',
            'app.payment_failed': 'El pago falló. Por favor inténtalo de nuevo.',
            'app.checkout_error': 'No se pudo crear el pago.',
            'nav.dashboard': 'Panel',
            'nav.chats': 'Charlas',
            'nav.billing': 'Facturación',
            'nav.settings': 'Ajustes',
            'nav.plan_remaining': 'Plan: {plan} · Restante: {chars}',
            'dashboard.title': 'Panel',
            'dashboard.desc': 'Resumen de su cuota y actividad de traducción.',
            'dashboard.plan': 'Plan',
            'dashboard.remaining': 'Restante',
            'dashboard.default_lang': 'Idioma predeterminado',
            'dashboard.totals': 'Totales',
            'dashboard.requests': 'Solicitudes: {n}',
            'dashboard.chars': 'Caracteres: {n}',
            'billing.title': 'Facturación',
            'billing.desc': 'Mejora tu cuota mensual con Telegram Stars.',
            'billing.chars_month': '{n} caracteres/mes',
            'billing.stars': '{n} estrellas',
            'billing.current_plan': 'Plan actual',
            'billing.pay_stars': 'Paga con estrellas',
            'chats.title': 'Charlas',
            'chats.desc': 'Administre reglas de traducción automática para chats de Telegram.',
            'chats.username_label': 'Nombre de usuario del chat',
            'chats.username_placeholder': 'devs_mundo',
            'chats.source': 'Fuente',
            'chats.target': 'Objetivo',
            'chats.limit_reached': 'Se alcanzó el límite de chat para tu plan.',
            'chats.can_add': 'Puedes agregar un nuevo chat de traducción automática.',
            'chats.add_btn': 'Agregar chat',
            'chats.table_chat': 'Chat',
            'chats.table_langs': 'Idiomas',
            'chats.table_status': 'Estado',
            'chats.empty': 'Aún no hay chats de traducción automática. Agregue uno arriba (nombre de usuario público sin @).',
            'settings.title': 'Ajustes',
            'settings.desc': 'Configure sus preferencias de traducción predeterminadas.',
            'settings.target_lang': 'Idioma de destino',
            'settings.favorite_langs': 'Idiomas favoritos',
            'settings.engine': 'Motor de traducción',
            'settings.engine_auto': 'Auto',
            'settings.engine_google': 'Google Free',
            'settings.engine_deepl': 'DeepL',
            'settings.save_btn': 'Guardar cambios',
            'settings.ui_language': 'Idioma de la interfaz',
            'settings.ui_lang_ru': 'Русский',
            'settings.ui_lang_en': 'English',
            'settings.ui_lang_uk': 'Українська',
            'qt.title': 'Traducción rápida',
            'qt.text_label': 'Texto',
            'qt.text_placeholder': 'Escribe algo para traducir...',
            'qt.source': 'Fuente',
            'qt.target': 'Objetivo',
            'qt.engine': 'Motor',
            'qt.translate_btn': 'Traducir',
            'qt.chars_left': 'Quedan {n} caracteres',
            'qt.from_cache': 'Desde caché ·',
            'qt.failed': 'La traducción falló.',
            'qt.result': 'Resultado',
            'qt.provider': '{provider} · {lang} detectado',
            'qt.copy': 'Copiar',
            'qt.copied': '¡Copiado!',
            'quota.title': 'Cuota mensual',
            'quota.used': '{used} / {limit} caracteres usados',
            'stats.chars': 'Uso de caracteres',
            'lang.not_found': 'No se encontraron idiomas',
            'langpicker.title': '¡Bienvenido! Elige tu idioma',
            'langpicker.desc': 'Seleccione el idioma de su interfaz. Puedes cambiarlo más tarde en Configuración.',
            'langpicker.en': 'Inglés',
            'langpicker.ru': 'Ruso',
            'langpicker.uk': 'Ucraniano',
            'langpicker.continue': 'Continuar',
        },
        'it': {
            'app.loading': 'Inizializzazione di TransApp...',
            'app.error.title': 'Mini app TransApp',
            'app.auth_failed': 'Autorizzazione fallita.',
            'app.init_error': "Impossibile inizializzare l'app.",
            'app.save_error': 'Impossibile salvare le impostazioni.',
            'app.chat_create_error': 'Impossibile creare la chat.',
            'app.chat_update_error': 'Impossibile aggiornare la chat.',
            'app.chat_delete_error': 'Impossibile eliminare la chat.',
            'app.payment_failed': 'Pagamento non riuscito. Per favore riprova.',
            'app.checkout_error': 'Impossibile creare il pagamento.',
            'nav.dashboard': 'Dashboard',
            'nav.chats': 'Chat',
            'nav.billing': 'Fatturazione',
            'nav.settings': 'Impostazioni',
            'nav.plan_remaining': 'Piano: {plan} · Rimanente: {chars}',
            'dashboard.title': 'Dashboard',
            'dashboard.desc': "Panoramica della quota e dell'attività di traduzione.",
            'dashboard.plan': 'Piano',
            'dashboard.remaining': 'Rimanente',
            'dashboard.default_lang': 'Lingua predefinita',
            'dashboard.totals': 'Totali',
            'dashboard.requests': 'Richieste: {n}',
            'dashboard.chars': 'Caratteri: {n}',
            'billing.title': 'Fatturazione',
            'billing.desc': 'Aggiorna la tua quota mensile con Telegram Stars.',
            'billing.chars_month': '{n} caratteri/mese',
            'billing.stars': '{n} Stelle',
            'billing.current_plan': 'Piano attuale',
            'billing.pay_stars': 'Paga con le stelle',
            'chats.title': 'Chat',
            'chats.desc': 'Gestisci le regole di traduzione automatica per le chat di Telegram.',
            'chats.username_label': 'Nome utente della chat',
            'chats.username_placeholder': 'devs_world',
            'chats.source': 'Fonte',
            'chats.target': 'Destinazione',
            'chats.limit_reached': 'Limite di chat raggiunto per il tuo piano.',
            'chats.can_add': 'Puoi aggiungere una nuova chat con traduzione automatica.',
            'chats.add_btn': 'Aggiungi chat',
            'chats.table_chat': 'Chat',
            'chats.table_langs': 'Lingue',
            'chats.table_status': 'Stato',
            'chats.empty': 'Nessuna chat con traduzione automatica ancora. Aggiungine uno sopra (nome utente pubblico senza @).',
            'settings.title': 'Impostazioni',
            'settings.desc': 'Configura le tue preferenze di traduzione predefinite.',
            'settings.target_lang': 'Lingua di destinazione',
            'settings.favorite_langs': 'Lingue preferite',
            'settings.engine': 'Motore di traduzione',
            'settings.engine_auto': 'Auto',
            'settings.engine_google': 'Google Free',
            'settings.engine_deepl': 'DeepL',
            'settings.save_btn': 'Salva modifiche',
            'settings.ui_language': 'Lingua dell\'interfaccia',
            'settings.ui_lang_ru': 'Русский',
            'settings.ui_lang_en': 'English',
            'settings.ui_lang_uk': 'Українська',
            'qt.title': 'Traduzione veloce',
            'qt.text_label': 'Testo',
            'qt.text_placeholder': 'Digita qualcosa da tradurre...',
            'qt.source': 'Fonte',
            'qt.target': 'Destinazione',
            'qt.engine': 'Motore',
            'qt.translate_btn': 'Traduci',
            'qt.chars_left': '{n} caratteri rimasti',
            'qt.from_cache': 'Dalla cache ·',
            'qt.failed': 'Traduzione fallita.',
            'qt.result': 'Risultato',
            'qt.provider': '{provider} · {lang} rilevato',
            'qt.copy': 'Copia',
            'qt.copied': 'Copiato!',
            'quota.title': 'Quota mensile',
            'quota.used': '{used} / {limit} caratteri utilizzati',
            'stats.chars': 'Utilizzo dei caratteri',
            'lang.not_found': 'Nessuna lingua trovata',
            'langpicker.title': 'Benvenuto! Scegli la tua lingua',
            'langpicker.desc': "Seleziona la lingua dell'interfaccia. Puoi modificarlo in seguito in Impostazioni.",
            'langpicker.en': 'Inglese',
            'langpicker.ru': 'Russo',
            'langpicker.uk': 'Ucraino',
            'langpicker.continue': 'Continua',
        },
        'pt': {
            'app.loading': 'Inicializando o TransApp...',
            'app.error.title': 'Miniaplicativo TransApp',
            'app.auth_failed': 'Falha na autorização.',
            'app.init_error': 'Falha ao inicializar o aplicativo.',
            'app.save_error': 'Falha ao salvar as configurações.',
            'app.chat_create_error': 'Falha ao criar bate-papo.',
            'app.chat_update_error': 'Falha ao atualizar o bate-papo.',
            'app.chat_delete_error': 'Falha ao excluir o bate-papo.',
            'app.payment_failed': 'Falha no pagamento. Por favor, tente novamente.',
            'app.checkout_error': 'Falha ao criar checkout.',
            'nav.dashboard': 'Painel',
            'nav.chats': 'Bate-papos',
            'nav.billing': 'Cobrança',
            'nav.settings': 'Configurações',
            'nav.plan_remaining': 'Plano: {plan} · Restante: {chars}',
            'dashboard.title': 'Painel',
            'dashboard.desc': 'Visão geral da sua cota e atividade de tradução.',
            'dashboard.plan': 'Plano',
            'dashboard.remaining': 'Restante',
            'dashboard.default_lang': 'Idioma padrão',
            'dashboard.totals': 'Totais',
            'dashboard.requests': 'Solicitações: {n}',
            'dashboard.chars': 'Caracteres: {n}',
            'billing.title': 'Cobrança',
            'billing.desc': 'Atualize sua cota mensal com Telegram Stars.',
            'billing.chars_month': '{n} caracteres/mês',
            'billing.stars': '{n} Estrelas',
            'billing.current_plan': 'Plano atual',
            'billing.pay_stars': 'Pague com estrelas',
            'chats.title': 'Bate-papos',
            'chats.desc': 'Gerencie regras de tradução automática para chats do Telegram.',
            'chats.username_label': 'Nome de usuário do bate-papo',
            'chats.username_placeholder': 'devs_world',
            'chats.source': 'Fonte',
            'chats.target': 'Alvo',
            'chats.limit_reached': 'O limite de bate-papo do seu plano foi atingido.',
            'chats.can_add': 'Você pode adicionar um novo chat de tradução automática.',
            'chats.add_btn': 'Adicionar bate-papo',
            'chats.table_chat': 'Bate-papo',
            'chats.table_langs': 'Idiomas',
            'chats.table_status': 'Status',
            'chats.empty': 'Ainda não há bate-papos com tradução automática. Adicione um acima (nome de usuário público sem @).',
            'settings.title': 'Configurações',
            'settings.desc': 'Configure suas preferências de tradução padrão.',
            'settings.target_lang': 'Idioma alvo',
            'settings.favorite_langs': 'Idiomas favoritos',
            'settings.engine': 'Mecanismo de tradução',
            'settings.engine_auto': 'Auto',
            'settings.engine_google': 'Google Grátis',
            'settings.engine_deepl': 'DeepL',
            'settings.save_btn': 'Salvar alterações',
            'settings.ui_language': 'Idioma da interface',
            'settings.ui_lang_ru': 'Русский',
            'settings.ui_lang_en': 'English',
            'settings.ui_lang_uk': 'Українська',
            'qt.title': 'Tradução rápida',
            'qt.text_label': 'Texto',
            'qt.text_placeholder': 'Digite algo para traduzir...',
            'qt.source': 'Fonte',
            'qt.target': 'Alvo',
            'qt.engine': 'Motor',
            'qt.translate_btn': 'Traduzir',
            'qt.chars_left': '{n} caracteres restantes',
            'qt.from_cache': 'Do cache ·',
            'qt.failed': 'A tradução falhou.',
            'qt.result': 'Resultado',
            'qt.provider': '{provider} · {lang} detectado',
            'qt.copy': 'Copiar',
            'qt.copied': 'Copiado!',
            'quota.title': 'Cota mensal',
            'quota.used': '{used} / {limit} caracteres usados',
            'stats.chars': 'Uso de caracteres',
            'lang.not_found': 'Nenhum idioma encontrado',
            'langpicker.title': 'Bem-vindo! Escolha seu idioma',
            'langpicker.desc': 'Selecione o idioma da sua interface. Você pode alterá-lo mais tarde em Configurações.',
            'langpicker.en': 'Inglês',
            'langpicker.ru': 'Russo',
            'langpicker.uk': 'Ucraniano',
            'langpicker.continue': 'Continuar',
        },
        'pl': {
            'app.loading': 'Inicjowanie TransApp...',
            'app.error.title': 'Miniaplikacja TransApp',
            'app.auth_failed': 'Autoryzacja nie powiodła się.',
            'app.init_error': 'Nie udało się zainicjować aplikacji.',
            'app.save_error': 'Nie udało się zapisać ustawień.',
            'app.chat_create_error': 'Nie udało się utworzyć czatu.',
            'app.chat_update_error': 'Nie udało się zaktualizować czatu.',
            'app.chat_delete_error': 'Nie udało się usunąć czatu.',
            'app.payment_failed': 'Płatność nie powiodła się. Spróbuj ponownie.',
            'app.checkout_error': 'Nie udało się utworzyć kasy.',
            'nav.dashboard': 'Panel',
            'nav.chats': 'Czaty',
            'nav.billing': 'Rozliczenia',
            'nav.settings': 'Ustawienia',
            'nav.plan_remaining': 'Plan: {plan} · Pozostało: {chars}',
            'dashboard.title': 'Panel',
            'dashboard.desc': 'Przegląd limitu tłumaczeń i aktywności.',
            'dashboard.plan': 'Plan',
            'dashboard.remaining': 'Pozostało',
            'dashboard.default_lang': 'Domyślny język',
            'dashboard.totals': 'Sumy',
            'dashboard.requests': 'Żądania: {n}',
            'dashboard.chars': 'Znaki: {n}',
            'billing.title': 'Rozliczenia',
            'billing.desc': 'Zwiększ swój miesięczny limit dzięki Telegram Stars.',
            'billing.chars_month': '{n} znaków/miesiąc',
            'billing.stars': '{n} Gwiazdy',
            'billing.current_plan': 'Aktualny plan',
            'billing.pay_stars': 'Płać gwiazdkami',
            'chats.title': 'Czaty',
            'chats.desc': 'Zarządzaj regułami automatycznego tłumaczenia czatów Telegram.',
            'chats.username_label': 'Nazwa użytkownika czatu',
            'chats.username_placeholder': 'devs_world',
            'chats.source': 'Źródło',
            'chats.target': 'Cel',
            'chats.limit_reached': 'Osiągnięto limit czatów dla Twojego planu.',
            'chats.can_add': 'Możesz dodać nowy czat z automatycznym tłumaczeniem.',
            'chats.add_btn': 'Dodaj czat',
            'chats.table_chat': 'Czat',
            'chats.table_langs': 'Języki',
            'chats.table_status': 'Status',
            'chats.empty': 'Nie ma jeszcze czatów z automatycznym tłumaczeniem. Dodaj jeden powyżej (publiczna nazwa użytkownika bez @).',
            'settings.title': 'Ustawienia',
            'settings.desc': 'Skonfiguruj domyślne preferencje tłumaczenia.',
            'settings.target_lang': 'Język docelowy',
            'settings.favorite_langs': 'Ulubione języki',
            'settings.engine': 'Silnik tłumaczeniowy',
            'settings.engine_auto': 'Auto',
            'settings.engine_google': 'Google Free',
            'settings.engine_deepl': 'DeepL',
            'settings.save_btn': 'Zapisz zmiany',
            'settings.ui_language': 'Język interfejsu',
            'settings.ui_lang_ru': 'Русский',
            'settings.ui_lang_en': 'English',
            'settings.ui_lang_uk': 'Українська',
            'qt.title': 'Szybkie tłumaczenie',
            'qt.text_label': 'Tekst',
            'qt.text_placeholder': 'Wpisz coś do przetłumaczenia...',
            'qt.source': 'Źródło',
            'qt.target': 'Cel',
            'qt.engine': 'Silnik',
            'qt.translate_btn': 'Tłumacz',
            'qt.chars_left': 'Pozostało {n} znaków',
            'qt.from_cache': 'Z pamięci podręcznej ·',
            'qt.failed': 'Tłumaczenie nie powiodło się.',
            'qt.result': 'Wynik',
            'qt.provider': '{provider} · wykryto {lang}',
            'qt.copy': 'Kopiuj',
            'qt.copied': 'Skopiowano!',
            'quota.title': 'Limit miesięczny',
            'quota.used': 'Użyto {used} / {limit} znaków',
            'stats.chars': 'Użycie znaków',
            'lang.not_found': 'Nie znaleziono języków',
            'langpicker.title': 'Witaj! Wybierz swój język',
            'langpicker.desc': 'Wybierz język interfejsu. Możesz to zmienić później w Ustawieniach.',
            'langpicker.en': 'Angielski',
            'langpicker.ru': 'Rosyjski',
            'langpicker.uk': 'Ukraiński',
            'langpicker.continue': 'Kontynuuj',
        },
        'tr': {
            'app.loading': 'TransApp başlatılıyor...',
            'app.error.title': 'TransApp Mini Uygulaması',
            'app.auth_failed': 'Yetkilendirme başarısız oldu.',
            'app.init_error': 'Uygulama başlatılamadı.',
            'app.save_error': 'Ayarlar kaydedilemedi.',
            'app.chat_create_error': 'Sohbet oluşturulamadı.',
            'app.chat_update_error': 'Sohbet güncellenemedi.',
            'app.chat_delete_error': 'Sohbet silinemedi.',
            'app.payment_failed': 'Ödeme başarısız oldu. Lütfen tekrar deneyin.',
            'app.checkout_error': 'Ödeme oluşturulamadı.',
            'nav.dashboard': 'Kontrol Paneli',
            'nav.chats': 'Sohbetler',
            'nav.billing': 'Faturalandırma',
            'nav.settings': 'Ayarlar',
            'nav.plan_remaining': 'Plan: {plan} · Kalan: {chars}',
            'dashboard.title': 'Kontrol Paneli',
            'dashboard.desc': 'Çeviri kotanıza ve etkinliğinize genel bakış.',
            'dashboard.plan': 'Plan',
            'dashboard.remaining': 'Kalan',
            'dashboard.default_lang': 'Varsayılan dil',
            'dashboard.totals': 'Toplamlar',
            'dashboard.requests': 'İstekler: {n}',
            'dashboard.chars': 'Karakterler: {n}',
            'billing.title': 'Faturalandırma',
            'billing.desc': 'Aylık kotanızı Telegram Stars ile yükseltin.',
            'billing.chars_month': '{n} karakter/ay',
            'billing.stars': '{n} Yıldız',
            'billing.current_plan': 'Mevcut plan',
            'billing.pay_stars': 'Yıldızlarla Öde',
            'chats.title': 'Sohbetler',
            'chats.desc': 'Telegram sohbetleri için otomatik çeviri kurallarını yönetin.',
            'chats.username_label': 'Sohbet kullanıcı adı',
            'chats.username_placeholder': 'devs_world',
            'chats.source': 'Kaynak',
            'chats.target': 'Hedef',
            'chats.limit_reached': 'Planınız için sohbet sınırına ulaşıldı.',
            'chats.can_add': 'Yeni bir otomatik çeviri sohbeti ekleyebilirsiniz.',
            'chats.add_btn': 'Sohbet ekle',
            'chats.table_chat': 'Sohbet',
            'chats.table_langs': 'Diller',
            'chats.table_status': 'Durum',
            'chats.empty': 'Henüz otomatik çeviri sohbeti yok. Yukarıya bir tane ekleyin (@ olmadan genel kullanıcı adı).',
            'settings.title': 'Ayarlar',
            'settings.desc': 'Varsayılan çeviri tercihlerinizi yapılandırın.',
            'settings.target_lang': 'Hedef dil',
            'settings.favorite_langs': 'Favori diller',
            'settings.engine': 'Çeviri motoru',
            'settings.engine_auto': 'Otomatik',
            'settings.engine_google': 'Google Free',
            'settings.engine_deepl': 'DeepL',
            'settings.save_btn': 'Değişiklikleri kaydet',
            'settings.ui_language': 'Arayüz dili',
            'settings.ui_lang_ru': 'Русский',
            'settings.ui_lang_en': 'English',
            'settings.ui_lang_uk': 'Українська',
            'qt.title': 'Hızlı çeviri',
            'qt.text_label': 'Metin',
            'qt.text_placeholder': 'Çevrilecek bir şey yazın...',
            'qt.source': 'Kaynak',
            'qt.target': 'Hedef',
            'qt.engine': 'Motor',
            'qt.translate_btn': 'Çevir',
            'qt.chars_left': '{n} karakter kaldı',
            'qt.from_cache': 'Önbellekten ·',
            'qt.failed': 'Çeviri başarısız oldu.',
            'qt.result': 'Sonuç',
            'qt.provider': '{provider} · {lang} algılandı',
            'qt.copy': 'Kopyala',
            'qt.copied': 'Kopyalandı!',
            'quota.title': 'Aylık kota',
            'quota.used': '{used} / {limit} karakter kullanıldı',
            'stats.chars': 'Karakter kullanımı',
            'lang.not_found': 'Dil bulunamadı',
            'langpicker.title': 'Hoş geldin! Dilinizi seçin',
            'langpicker.desc': 'Arayüz dilinizi seçin. Bunu daha sonra Ayarlar\'dan değiştirebilirsiniz.',
            'langpicker.continue': 'Devam',
        },
    }

    LANG_NAMES = {
        'de': {
            'auto': 'Automatische Erkennung',
            'en': 'Englisch',
            'ru': 'Russisch',
            'uk': 'Ukrainisch',
            'de': 'Deutsch',
            'fr': 'Französisch',
            'es': 'Spanisch',
            'it': 'Italienisch',
            'pl': 'Polnisch',
            'pt': 'Portugiesisch',
            'tr': 'Türkisch',
            'zh': 'Chinesisch',
            'ja': 'Japanisch',
        },
        'fr': {
            'auto': 'Détection automatique',
            'en': 'Anglais',
            'ru': 'Russe',
            'uk': 'Ukrainien',
            'de': 'Allemand',
            'fr': 'Français',
            'es': 'Espagnol',
            'it': 'Italien',
            'pl': 'Polonais',
            'pt': 'Portugais',
            'tr': 'Turc',
            'zh': 'Chinois',
            'ja': 'Japonais',
        },
        'es': {
            'auto': 'Detección automática',
            'en': 'Inglés',
            'ru': 'Ruso',
            'uk': 'Ucraniano',
            'de': 'Alemán',
            'fr': 'Francés',
            'es': 'Español',
            'it': 'Italiano',
            'pl': 'Polaco',
            'pt': 'Portugués',
            'tr': 'Turco',
            'zh': 'Chino',
            'ja': 'Japonés',
        },
        'it': {
            'auto': 'Rilevamento automatico',
            'en': 'Inglese',
            'ru': 'Russo',
            'uk': 'Ucraino',
            'de': 'Tedesco',
            'fr': 'Francese',
            'es': 'Spagnolo',
            'it': 'Italiano',
            'pl': 'Polacco',
            'pt': 'Portoghese',
            'tr': 'Turco',
            'zh': 'Cinese',
            'ja': 'Giapponese',
        },
        'pt': {
            'auto': 'Detecção automática',
            'en': 'Inglês',
            'ru': 'Russo',
            'uk': 'Ucraniano',
            'de': 'Alemão',
            'fr': 'Francês',
            'es': 'Espanhol',
            'it': 'Italiano',
            'pl': 'Polonês',
            'pt': 'Português',
            'tr': 'Turco',
            'zh': 'Chinês',
            'ja': 'Japonês',
        },
        'pl': {
            'auto': 'Automatyczne wykrywanie',
            'en': 'Angielski',
            'ru': 'Rosyjski',
            'uk': 'Ukraiński',
            'de': 'Niemiecki',
            'fr': 'Francuski',
            'es': 'Hiszpański',
            'it': 'Włoski',
            'pl': 'Polski',
            'pt': 'Portugalski',
            'tr': 'Turecki',
            'zh': 'Chiński',
            'ja': 'Japoński',
        },
        'tr': {
            'auto': 'Otomatik algılama',
            'en': 'İngilizce',
            'ru': 'Rusça',
            'uk': 'Ukraynaca',
            'de': 'Almanca',
            'fr': 'Fransızca',
            'es': 'İspanyolca',
            'it': 'İtalyanca',
            'pl': 'Lehçe',
            'pt': 'Portekizce',
            'tr': 'Türkçe',
            'zh': 'Çince',
            'ja': 'Japonca',
        },
    }

    # Read the current file
    with open(i18n_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the end of the LOCALES section (after EN, before LANG_NAMES)
    # We'll find the end of the en: { ... } block
    # Locate where new languages should be inserted (before `};` closing LOCALES)
    
    # Find the LOCALES section end and LANG_NAMES section end
    # The closing of LOCALES is `};\n` that appears after all languages
    
    # Read the file and reconstruct it
    lines = content.split('\n')
    
    # Find the key insertion points
    locales_close_line = None
    lang_names_close_line = None
    
    # We need to find:
    # 1. Where to insert new LOCALES entries (before "};\n" after en block)
    # 2. Where to insert new LANG_NAMES entries (before "};\n" after en block)
    
    # Strategy: find the last `},` before `};` for LOCALES
    # and the last `},` before `};` for LANG_NAMES
    
    # Find all lines that close a language block in LOCALES
    # Pattern: after en block, there's `},` then `};`
    # We want to insert new languages right before `};`
    
    output_lines = []
    in_locales = False
    in_lang_names = False
    locales_done = False
    lang_names_done = False
    current_lang_block = None
    
    for i, line in enumerate(lines):
        if line.strip() == 'export const LOCALES: Record<string, Record<string, string>> = {':
            in_locales = True
            output_lines.append(line)
            continue
        
        if in_locales and not locales_done:
            if line.strip() == '};' and not line.strip().startswith('  /*'):
                # Before closing LOCALES, insert new languages
                # Insert de, fr, es, it, pt, pl, tr
                for lang in ['de', 'fr', 'es', 'it', 'pt', 'pl', 'tr']:
                    output_lines.append(f'  {lang}: {{')
                    keys = sorted(LOCALES[lang].keys())
                    for k in keys:
                        v = LOCALES[lang][k]
                        escaped = v.replace("'", "\\'")
                        output_lines.append(f"    '{k}': '{escaped}',")
                    output_lines.append('  },')
                output_lines.append(line)
                locales_done = True
                in_locales = False
                continue
            
            if line.strip() == 'en: {':
                output_lines.append(line)
                continue
            
            if line.strip() == '},' and current_lang_block == 'en':
                output_lines.append(line)
                current_lang_block = None
                continue
            
            if line.strip() == '}':
                # Could be end of a lang block or something else
                pass
            
            output_lines.append(line)
            continue
        
        if line.strip() == 'export const LANG_NAMES_LOCALIZED: Record<string, Record<string, string>> = {':
            in_lang_names = True
            output_lines.append(line)
            continue
        
        if in_lang_names and not lang_names_done:
            if line.strip() == '};':
                for lang in ['de', 'fr', 'es', 'it', 'pt', 'pl', 'tr']:
                    output_lines.append(f'  {lang}: {{')
                    keys = sorted(LANG_NAMES[lang].keys())
                    for k in keys:
                        v = LANG_NAMES[lang][k]
                        escaped = v.replace("'", "\\'")
                        output_lines.append(f"    {k}: '{escaped}',")
                    output_lines.append('  },')
                output_lines.append(line)
                lang_names_done = True
                in_lang_names = False
                continue
            
            if line.strip() == 'en: {':
                output_lines.append(line)
                continue
            
            if line.strip() == '},' and current_lang_block == 'en_names':
                output_lines.append(line)
                current_lang_block = None
                continue
            
            output_lines.append(line)
            continue
        
        output_lines.append(line)
    
    result = '\n'.join(output_lines)
    
    with open(i18n_path, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"Updated {i18n_path}")
    print(f"Added locales: de, fr, es, it, pt, pl, tr")
    print(f"Added lang names: de, fr, es, it, pt, pl, tr")


if __name__ == '__main__':
    generate_i18n_content()
