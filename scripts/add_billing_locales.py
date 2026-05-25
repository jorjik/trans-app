"""Добавляет ключи локализации для Ko-fi и PayPal во все 10 файлов."""

import json
import os
import glob

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "bot", "locales")

# Ключи с переводами для каждого языка
NEW_KEYS = {
    "en": {
        "billing_choose_method": "Choose payment method for <b>{plan}</b> ({price_stars} ⭐):",
        "billing_method_stars": "⭐ Telegram Stars",
        "billing_method_kofi": "☕ Ko-fi",
        "billing_method_paypal": "💳 PayPal",
        "billing_kofi_instructions": "☕ <b>Pay with Ko-fi</b>\n\nPlan: <b>{plan}</b>\nAmount: <b>{amount} {currency}</b>\n\n1. Click the button below\n2. Enter amount <b>{amount}</b> {currency}\n3. In the message field, enter your code: <code>{code}</code>\n4. Complete payment\n\nAfter payment, the plan will be activated automatically.",
        "billing_kofi_open": "☕ Open Ko-fi",
        "billing_paypal_instructions": "💳 <b>Pay with PayPal</b>\n\nPlan: <b>{plan}</b>\nAmount: <b>{amount} {currency}</b>\n\n1. Click «Approve on PayPal»\n2. Log in and confirm the payment\n3. Come back and click «Check payment»",
        "billing_paypal_approve": "💳 Approve on PayPal",
        "billing_paypal_check": "🔄 Check payment",
        "billing_paypal_pending": "⏳ <b>Waiting for payment...</b>\n\nPlease approve the payment on PayPal, then click «Check payment».",
        "billing_paypal_success": "✅ <b>Payment received!</b>\n\nPlan <b>{plan}</b> activated!\nThank you for your support! 🙏",
        "billing_paypal_error": "❌ Payment failed or was cancelled. Please try again.",
        "billing_generic_error": "❌ Something went wrong. Please try again later.",
        "plan_starter": "Starter",
        "plan_pro": "Pro",
        "plan_business": "Business",
    },
    "ru": {
        "billing_choose_method": "Выберите способ оплаты для <b>{plan}</b> ({price_stars} ⭐):",
        "billing_method_stars": "⭐ Telegram Stars",
        "billing_method_kofi": "☕ Ko-fi",
        "billing_method_paypal": "💳 PayPal",
        "billing_kofi_instructions": "☕ <b>Оплата через Ko-fi</b>\n\nТариф: <b>{plan}</b>\nСумма: <b>{amount} {currency}</b>\n\n1. Нажмите кнопку ниже\n2. Введите сумму <b>{amount}</b> {currency}\n3. В поле сообщения укажите код: <code>{code}</code>\n4. Завершите оплату\n\nПосле оплаты тариф активируется автоматически.",
        "billing_kofi_open": "☕ Открыть Ko-fi",
        "billing_paypal_instructions": "💳 <b>Оплата через PayPal</b>\n\nТариф: <b>{plan}</b>\nСумма: <b>{amount} {currency}</b>\n\n1. Нажмите «Подтвердить в PayPal»\n2. Войдите и подтвердите платёж\n3. Вернитесь и нажмите «Проверить оплату»",
        "billing_paypal_approve": "💳 Подтвердить в PayPal",
        "billing_paypal_check": "🔄 Проверить оплату",
        "billing_paypal_pending": "⏳ <b>Ожидание оплаты...</b>\n\nПожалуйста, подтвердите платёж в PayPal, затем нажмите «Проверить оплату».",
        "billing_paypal_success": "✅ <b>Оплата получена!</b>\n\nТариф <b>{plan}</b> активирован!\nСпасибо за поддержку! 🙏",
        "billing_paypal_error": "❌ Платёж не удался или отменён. Попробуйте снова.",
        "billing_generic_error": "❌ Что-то пошло не так. Попробуйте позже.",
        "plan_starter": "Starter",
        "plan_pro": "Pro",
        "plan_business": "Business",
    },
    "uk": {
        "billing_choose_method": "Виберіть спосіб оплати для <b>{plan}</b> ({price_stars} ⭐):",
        "billing_method_stars": "⭐ Telegram Stars",
        "billing_method_kofi": "☕ Ko-fi",
        "billing_method_paypal": "💳 PayPal",
        "billing_kofi_instructions": "☕ <b>Оплата через Ko-fi</b>\n\nТариф: <b>{plan}</b>\nСума: <b>{amount} {currency}</b>\n\n1. Натисніть кнопку нижче\n2. Введіть суму <b>{amount}</b> {currency}\n3. У полі повідомлення вкажіть код: <code>{code}</code>\n4. Завершіть оплату\n\nПісля оплати тариф активується автоматично.",
        "billing_kofi_open": "☕ Відкрити Ko-fi",
        "billing_paypal_instructions": "💳 <b>Оплата через PayPal</b>\n\nТариф: <b>{plan}</b>\nСума: <b>{amount} {currency}</b>\n\n1. Натисніть «Підтвердити в PayPal»\n2. Увійдіть та підтвердьте платіж\n3. Поверніться та натисніть «Перевірити оплату»",
        "billing_paypal_approve": "💳 Підтвердити в PayPal",
        "billing_paypal_check": "🔄 Перевірити оплату",
        "billing_paypal_pending": "⏳ <b>Очікування оплати...</b>\n\nБудь ласка, підтвердьте платіж у PayPal, потім натисніть «Перевірити оплату».",
        "billing_paypal_success": "✅ <b>Оплату отримано!</b>\n\nТариф <b>{plan}</b> активовано!\nДякуємо за підтримку! 🙏",
        "billing_paypal_error": "❌ Платіж не вдався або скасовано. Спробуйте ще раз.",
        "billing_generic_error": "❌ Щось пішло не так. Спробуйте пізніше.",
        "plan_starter": "Starter",
        "plan_pro": "Pro",
        "plan_business": "Business",
    },
    "de": {
        "billing_choose_method": "Wählen Sie eine Zahlungsmethode für <b>{plan}</b> ({price_stars} ⭐):",
        "billing_method_stars": "⭐ Telegram Stars",
        "billing_method_kofi": "☕ Ko-fi",
        "billing_method_paypal": "💳 PayPal",
        "billing_kofi_instructions": "☕ <b>Zahlung mit Ko-fi</b>\n\nTarif: <b>{plan}</b>\nBetrag: <b>{amount} {currency}</b>\n\n1. Klicken Sie auf den Button unten\n2. Geben Sie den Betrag <b>{amount}</b> {currency} ein\n3. Geben Sie im Nachrichtenfeld den Code ein: <code>{code}</code>\n4. Schließen Sie die Zahlung ab\n\nNach der Zahlung wird der Tarif automatisch aktiviert.",
        "billing_kofi_open": "☕ Ko-fi öffnen",
        "billing_paypal_instructions": "💳 <b>Zahlung mit PayPal</b>\n\nTarif: <b>{plan}</b>\nBetrag: <b>{amount} {currency}</b>\n\n1. Klicken Sie auf «In PayPal bestätigen»\n2. Melden Sie sich an und bestätigen Sie die Zahlung\n3. Kommen Sie zurück und klicken Sie auf «Zahlung prüfen»",
        "billing_paypal_approve": "💳 In PayPal bestätigen",
        "billing_paypal_check": "🔄 Zahlung prüfen",
        "billing_paypal_pending": "⏳ <b>Warte auf Zahlung...</b>\n\nBitte bestätigen Sie die Zahlung in PayPal und klicken Sie dann auf «Zahlung prüfen».",
        "billing_paypal_success": "✅ <b>Zahlung erhalten!</b>\n\nTarif <b>{plan}</b> aktiviert!\nVielen Dank für Ihre Unterstützung! 🙏",
        "billing_paypal_error": "❌ Zahlung fehlgeschlagen oder abgebrochen. Bitte versuchen Sie es erneut.",
        "billing_generic_error": "❌ Etwas ist schiefgelaufen. Bitte versuchen Sie es später erneut.",
        "plan_starter": "Starter",
        "plan_pro": "Pro",
        "plan_business": "Business",
    },
    "fr": {
        "billing_choose_method": "Choisissez un moyen de paiement pour <b>{plan}</b> ({price_stars} ⭐):",
        "billing_method_stars": "⭐ Telegram Stars",
        "billing_method_kofi": "☕ Ko-fi",
        "billing_method_paypal": "💳 PayPal",
        "billing_kofi_instructions": "☕ <b>Payer avec Ko-fi</b>\n\nForfait: <b>{plan}</b>\nMontant: <b>{amount} {currency}</b>\n\n1. Cliquez sur le bouton ci-dessous\n2. Entrez le montant <b>{amount}</b> {currency}\n3. Dans le champ message, entrez votre code: <code>{code}</code>\n4. Terminez le paiement\n\nAprès le paiement, le forfait sera activé automatiquement.",
        "billing_kofi_open": "☕ Ouvrir Ko-fi",
        "billing_paypal_instructions": "💳 <b>Payer avec PayPal</b>\n\nForfait: <b>{plan}</b>\nMontant: <b>{amount} {currency}</b>\n\n1. Cliquez sur «Approuver sur PayPal»\n2. Connectez-vous et confirmez le paiement\n3. Revenez et cliquez sur «Vérifier le paiement»",
        "billing_paypal_approve": "💳 Approuver sur PayPal",
        "billing_paypal_check": "🔄 Vérifier le paiement",
        "billing_paypal_pending": "⏳ <b>En attente du paiement...</b>\n\nVeuillez approuver le paiement sur PayPal, puis cliquez sur «Vérifier le paiement».",
        "billing_paypal_success": "✅ <b>Paiement reçu!</b>\n\nForfait <b>{plan}</b> activé!\nMerci pour votre soutien! 🙏",
        "billing_paypal_error": "❌ Paiement échoué ou annulé. Veuillez réessayer.",
        "billing_generic_error": "❌ Quelque chose s'est mal passé. Veuillez réessayer plus tard.",
        "plan_starter": "Starter",
        "plan_pro": "Pro",
        "plan_business": "Business",
    },
    "es": {
        "billing_choose_method": "Elija un método de pago para <b>{plan}</b> ({price_stars} ⭐):",
        "billing_method_stars": "⭐ Telegram Stars",
        "billing_method_kofi": "☕ Ko-fi",
        "billing_method_paypal": "💳 PayPal",
        "billing_kofi_instructions": "☕ <b>Pagar con Ko-fi</b>\n\nPlan: <b>{plan}</b>\nMonto: <b>{amount} {currency}</b>\n\n1. Haga clic en el botón de abajo\n2. Ingrese el monto <b>{amount}</b> {currency}\n3. En el campo de mensaje, ingrese su código: <code>{code}</code>\n4. Complete el pago\n\nDespués del pago, el plan se activará automáticamente.",
        "billing_kofi_open": "☕ Abrir Ko-fi",
        "billing_paypal_instructions": "💳 <b>Pagar con PayPal</b>\n\nPlan: <b>{plan}</b>\nMonto: <b>{amount} {currency}</b>\n\n1. Haga clic en «Aprobar en PayPal»\n2. Inicie sesión y confirme el pago\n3. Vuelva y haga clic en «Verificar pago»",
        "billing_paypal_approve": "💳 Aprobar en PayPal",
        "billing_paypal_check": "🔄 Verificar pago",
        "billing_paypal_pending": "⏳ <b>Esperando pago...</b>\n\nApruebe el pago en PayPal, luego haga clic en «Verificar pago».",
        "billing_paypal_success": "✅ <b>¡Pago recibido!</b>\n\nPlan <b>{plan}</b> activado!\n¡Gracias por su apoyo! 🙏",
        "billing_paypal_error": "❌ Pago fallido o cancelado. Intente de nuevo.",
        "billing_generic_error": "❌ Algo salió mal. Intente de nuevo más tarde.",
        "plan_starter": "Starter",
        "plan_pro": "Pro",
        "plan_business": "Business",
    },
    "it": {
        "billing_choose_method": "Scegli un metodo di pagamento per <b>{plan}</b> ({price_stars} ⭐):",
        "billing_method_stars": "⭐ Telegram Stars",
        "billing_method_kofi": "☕ Ko-fi",
        "billing_method_paypal": "💳 PayPal",
        "billing_kofi_instructions": "☕ <b>Paga con Ko-fi</b>\n\nPiano: <b>{plan}</b>\nImporto: <b>{amount} {currency}</b>\n\n1. Clicca il pulsante qui sotto\n2. Inserisci l'importo <b>{amount}</b> {currency}\n3. Nel campo messaggio, inserisci il codice: <code>{code}</code>\n4. Completa il pagamento\n\nDopo il pagamento, il piano verrà attivato automaticamente.",
        "billing_kofi_open": "☕ Apri Ko-fi",
        "billing_paypal_instructions": "💳 <b>Paga con PayPal</b>\n\nPiano: <b>{plan}</b>\nImporto: <b>{amount} {currency}</b>\n\n1. Clicca «Approva su PayPal»\n2. Accedi e conferma il pagamento\n3. Torna e clicca «Verifica pagamento»",
        "billing_paypal_approve": "💳 Approva su PayPal",
        "billing_paypal_check": "🔄 Verifica pagamento",
        "billing_paypal_pending": "⏳ <b>In attesa del pagamento...</b>\n\nApprova il pagamento su PayPal, poi clicca «Verifica pagamento».",
        "billing_paypal_success": "✅ <b>Pagamento ricevuto!</b>\n\nPiano <b>{plan}</b> attivato!\nGrazie per il supporto! 🙏",
        "billing_paypal_error": "❌ Pagamento fallito o annullato. Riprova.",
        "billing_generic_error": "❌ Qualcosa è andato storto. Riprova più tardi.",
        "plan_starter": "Starter",
        "plan_pro": "Pro",
        "plan_business": "Business",
    },
    "pt": {
        "billing_choose_method": "Escolha um método de pagamento para <b>{plan}</b> ({price_stars} ⭐):",
        "billing_method_stars": "⭐ Telegram Stars",
        "billing_method_kofi": "☕ Ko-fi",
        "billing_method_paypal": "💳 PayPal",
        "billing_kofi_instructions": "☕ <b>Pagar com Ko-fi</b>\n\nPlano: <b>{plan}</b>\nValor: <b>{amount} {currency}</b>\n\n1. Clique no botão abaixo\n2. Insira o valor <b>{amount}</b> {currency}\n3. No campo de mensagem, insira seu código: <code>{code}</code>\n4. Finalize o pagamento\n\nApós o pagamento, o plano será ativado automaticamente.",
        "billing_kofi_open": "☕ Abrir Ko-fi",
        "billing_paypal_instructions": "💳 <b>Pagar com PayPal</b>\n\nPlano: <b>{plan}</b>\nValor: <b>{amount} {currency}</b>\n\n1. Clique em «Aprovar no PayPal»\n2. Faça login e confirme o pagamento\n3. Volte e clique em «Verificar pagamento»",
        "billing_paypal_approve": "💳 Aprovar no PayPal",
        "billing_paypal_check": "🔄 Verificar pagamento",
        "billing_paypal_pending": "⏳ <b>Aguardando pagamento...</b>\n\nAprove o pagamento no PayPal e clique em «Verificar pagamento».",
        "billing_paypal_success": "✅ <b>Pagamento recebido!</b>\n\nPlano <b>{plan}</b> ativado!\nObrigado pelo seu apoio! 🙏",
        "billing_paypal_error": "❌ Pagamento falhou ou foi cancelado. Tente novamente.",
        "billing_generic_error": "❌ Algo deu errado. Tente novamente mais tarde.",
        "plan_starter": "Starter",
        "plan_pro": "Pro",
        "plan_business": "Business",
    },
    "pl": {
        "billing_choose_method": "Wybierz metodę płatności dla <b>{plan}</b> ({price_stars} ⭐):",
        "billing_method_stars": "⭐ Telegram Stars",
        "billing_method_kofi": "☕ Ko-fi",
        "billing_method_paypal": "💳 PayPal",
        "billing_kofi_instructions": "☕ <b>Zapłać przez Ko-fi</b>\n\nPlan: <b>{plan}</b>\nKwota: <b>{amount} {currency}</b>\n\n1. Kliknij przycisk poniżej\n2. Wprowadź kwotę <b>{amount}</b> {currency}\n3. W polu wiadomości wpisz kod: <code>{code}</code>\n4. Zakończ płatność\n\nPo dokonaniu płatności plan zostanie automatycznie aktywowany.",
        "billing_kofi_open": "☕ Otwórz Ko-fi",
        "billing_paypal_instructions": "💳 <b>Zapłać przez PayPal</b>\n\nPlan: <b>{plan}</b>\nKwota: <b>{amount} {currency}</b>\n\n1. Kliknij «Zatwierdź w PayPal»\n2. Zaloguj się i potwierdź płatność\n3. Wróć i kliknij «Sprawdź płatność»",
        "billing_paypal_approve": "💳 Zatwierdź w PayPal",
        "billing_paypal_check": "🔄 Sprawdź płatność",
        "billing_paypal_pending": "⏳ <b>Oczekiwanie na płatność...</b>\n\nZatwierdź płatność w PayPal, a następnie kliknij «Sprawdź płatność».",
        "billing_paypal_success": "✅ <b>Płatność otrzymana!</b>\n\nPlan <b>{plan}</b> aktywowany!\nDziękujemy za wsparcie! 🙏",
        "billing_paypal_error": "❌ Płatność nie powiodła się lub została anulowana. Spróbuj ponownie.",
        "billing_generic_error": "❌ Coś poszło nie tak. Spróbuj ponownie później.",
        "plan_starter": "Starter",
        "plan_pro": "Pro",
        "plan_business": "Business",
    },
    "tr": {
        "billing_choose_method": "<b>{plan}</b> ({price_stars} ⭐) için ödeme yöntemi seçin:",
        "billing_method_stars": "⭐ Telegram Stars",
        "billing_method_kofi": "☕ Ko-fi",
        "billing_method_paypal": "💳 PayPal",
        "billing_kofi_instructions": "☕ <b>Ko-fi ile Öde</b>\n\nPlan: <b>{plan}</b>\nTutar: <b>{amount} {currency}</b>\n\n1. Aşağıdaki butona tıklayın\n2. <b>{amount}</b> {currency} tutarını girin\n3. Mesaj alanına kodunuzu girin: <code>{code}</code>\n4. Ödemeyi tamamlayın\n\nÖdeme sonrası plan otomatik olarak aktifleşir.",
        "billing_kofi_open": "☕ Ko-fi'yi Aç",
        "billing_paypal_instructions": "💳 <b>PayPal ile Öde</b>\n\nPlan: <b>{plan}</b>\nTutar: <b>{amount} {currency}</b>\n\n1. «PayPal'da Onayla»ya tıklayın\n2. Giriş yapın ve ödemeyi onaylayın\n3. Geri gelin ve «Ödemeyi Kontrol Et»e tıklayın",
        "billing_paypal_approve": "💳 PayPal'da Onayla",
        "billing_paypal_check": "🔄 Ödemeyi Kontrol Et",
        "billing_paypal_pending": "⏳ <b>Ödeme bekleniyor...</b>\n\nLütfen PayPal'da ödemeyi onaylayın, ardından «Ödemeyi Kontrol Et»e tıklayın.",
        "billing_paypal_success": "✅ <b>Ödeme alındı!</b>\n\n<b>{plan}</b> planı aktifleştirildi!\nDesteğiniz için teşekkürler! 🙏",
        "billing_paypal_error": "❌ Ödeme başarısız oldu veya iptal edildi. Lütfen tekrar deneyin.",
        "billing_generic_error": "❌ Bir şeyler yanlış gitti. Lütfen daha sonra tekrar deneyin.",
        "plan_starter": "Starter",
        "plan_pro": "Pro",
        "plan_business": "Business",
    },
}


def main():
    for filepath in sorted(glob.glob(os.path.join(LOCALES_DIR, "*.json"))):
        lang = os.path.splitext(os.path.basename(filepath))[0]
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        lang_keys = NEW_KEYS.get(lang, NEW_KEYS["en"])
        added = 0
        updated = 0
        for key, value in lang_keys.items():
            if key not in data:
                data[key] = value
                added += 1
            elif data[key] != value:
                # Only update plan names if they don't exist
                if key.startswith("plan_"):
                    if key not in data:
                        data[key] = value
                        added += 1
                else:
                    data[key] = value
                    updated += 1

        # Check for missing keys that exist in en but not in this lang
        for key in NEW_KEYS["en"]:
            if key not in data:
                data[key] = NEW_KEYS["en"][key]
                added += 1

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

        print(f"{lang}: added={added}, updated={updated}")


if __name__ == "__main__":
    main()
