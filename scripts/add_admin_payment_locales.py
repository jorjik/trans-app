"""Добавляет ключи локализации для настроек оплаты в админке."""

import json
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parent.parent / "bot" / "locales"

NEW_KEYS = {
    "admin_btn_payment": {
        "en": "💳 Payment Methods",
        "ru": "💳 Способы оплаты",
        "uk": "💳 Способи оплати",
        "de": "💳 Zahlungsmethoden",
        "fr": "💳 Méthodes de paiement",
        "es": "💳 Métodos de pago",
        "pl": "💳 Metody płatności",
        "it": "💳 Metodi di pagamento",
        "pt": "💳 Métodos de pagamento",
        "tr": "💳 Ödeme Yöntemleri",
    },
    "admin_payment_title": {
        "en": "💳 <b>Payment Methods Visibility</b>\n\nToggle which payment methods users can see when upgrading:\n\nTap a button to toggle on/off.",
        "ru": "💳 <b>Видимость способов оплаты</b>\n\nВключи/выключи какие способы оплаты видят пользователи:\n\nНажми кнопку чтобы включить/выключить.",
        "uk": "💳 <b>Видимість способів оплати</b>\n\nУвімкни/вимкни які способи оплати бачать користувачі:\n\nНатисни кнопку щоб увімкнути/вимкнути.",
        "de": "💳 <b>Sichtbarkeit der Zahlungsmethoden</b>\n\nLege fest, welche Zahlungsmethoden Benutzer sehen:\n\nTippe auf einen Knopf zum Ein-/Ausschalten.",
        "fr": "💳 <b>Visibilité des méthodes de paiement</b>\n\nActivez/désactivez les méthodes de paiement visibles :\n\nAppuyez sur un bouton pour activer/désactiver.",
        "es": "💳 <b>Visibilidad de métodos de pago</b>\n\nActiva/desactiva qué métodos ven los usuarios:\n\nToca un botón para activar/desactivar.",
        "pl": "💳 <b>Widoczność metod płatności</b>\n\nWłącz/wyłącz które metody płatności widzą użytkownicy:\n\nDotknij przycisk, aby włączyć/wyłączyć.",
        "it": "💳 <b>Visibilità metodi di pagamento</b>\n\nAttiva/disattiva quali metodi vedono gli utenti:\n\nTocca un pulsante per attivare/disattivare.",
        "pt": "💳 <b>Visibilidade dos métodos de pagamento</b>\n\nAtive/desative quais métodos os usuários veem:\n\nToque num botão para ativar/desativar.",
        "tr": "💳 <b>Ödeme Yöntemi Görünürlüğü</b>\n\nKullanıcıların hangi ödeme yöntemlerini göreceğini ayarlayın:\n\nAçıp kapatmak için bir düğmeye dokunun.",
    },
    "admin_payment_error": {
        "en": "❌ Failed to update payment settings. Try again.",
        "ru": "❌ Не удалось обновить настройки оплаты. Попробуйте ещё раз.",
        "uk": "❌ Не вдалося оновити налаштування оплати. Спробуйте ще раз.",
        "de": "❌ Zahlungseinstellungen konnten nicht aktualisiert werden. Versuche es erneut.",
        "fr": "❌ Échec de la mise à jour des paramètres de paiement. Réessayez.",
        "es": "❌ No se pudieron actualizar los ajustes de pago. Intente de nuevo.",
        "pl": "❌ Nie udało się zaktualizować ustawień płatności. Spróbuj ponownie.",
        "it": "❌ Impossibile aggiornare le impostazioni di pagamento. Riprova.",
        "pt": "❌ Falha ao atualizar as configurações de pagamento. Tente novamente.",
        "tr": "❌ Ödeme ayarları güncellenemedi. Tekrar deneyin.",
    },
}


def main():
    count = 0
    for locale_file in sorted(LOCALES_DIR.glob("*.json")):
        lang_code = locale_file.stem
        with open(locale_file, encoding="utf-8") as f:
            data = json.load(f)

        added = 0
        for key, translations in NEW_KEYS.items():
            if key not in data:
                data[key] = translations.get(lang_code, translations.get("en", ""))
                added += 1

        if added:
            with open(locale_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
            print(f"  {locale_file.name}: +{added} keys")
            count += added
        else:
            print(f"  {locale_file.name}: no changes")

    print(f"\nTotal: {count} keys added across all locale files")


if __name__ == "__main__":
    main()
