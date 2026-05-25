"""Add admin_paid_percent key to all 10 locale files."""
import json, os, sys

sys.stdout.reconfigure(encoding='utf-8')

LOCALES_DIR = os.path.join(os.path.dirname(__file__), '..', 'bot', 'locales')

TRANSLATIONS = {
    "en": "Paid: <b>{pct}%</b> ({count} users)",
    "ru": "Платных: <b>{pct}%</b> ({count} чел.)",
    "uk": "Платних: <b>{pct}%</b> ({count} осіб)",
    "de": "Bezahlt: <b>{pct}%</b> ({count} Nutzer)",
    "fr": "Payants : <b>{pct}%</b> ({count} utilisateurs)",
    "es": "De pago: <b>{pct}%</b> ({count} usuarios)",
    "it": "A pagamento: <b>{pct}%</b> ({count} utenti)",
    "pt": "Pagos: <b>{pct}%</b> ({count} usuários)",
    "pl": "Płatni: <b>{pct}%</b> ({count} użytkowników)",
    "tr": "Ücretli: <b>{pct}%</b> ({count} kullanıcı)",
}

for lang, text in TRANSLATIONS.items():
    filepath = os.path.join(LOCALES_DIR, f"{lang}.json")
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    data["admin_paid_percent"] = text
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"OK {lang}.json: added admin_paid_percent")
