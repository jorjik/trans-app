"""POST /webhook/telegram вЂ” РІС…РѕРґСЏС‰РёРµ Р°РїРґРµР№С‚С‹ РѕС‚ Telegram Bot API."""

import logging
from fastapi import APIRouter, Header, HTTPException, Request, status

from core.security import validate_webhook_secret

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/telegram", status_code=status.HTTP_200_OK)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None),
) -> dict:
    if not validate_webhook_secret(x_telegram_bot_api_secret_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid secret")

    body = await request.json()
    logger.debug("Webhook update: %s", body.get("update_id"))

    # Р’ production: РїРµСЂРµРґР°С‘Рј РІ Bot Service С‡РµСЂРµР· РѕС‡РµСЂРµРґСЊ РёР»Рё РЅР°РїСЂСЏРјСѓСЋ
    # РЎРµР№С‡Р°СЃ: РїСЂРѕСЃС‚Рѕ Р»РѕРіРёСЂСѓРµРј
    return {"ok": True}