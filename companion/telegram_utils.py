import logging
import os

import requests
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import TelegramProfile

logger = logging.getLogger(__name__)


def get_or_create_telegram_user(chat_id):
    profile = (
        TelegramProfile.objects.filter(chat_id=chat_id).select_related("user").first()
    )
    if profile:
        return profile.user
    with transaction.atomic():
        User = get_user_model()
        user = User.objects.create_user(email=f"tg_{chat_id}@telegram.local")
        user.set_unusable_password()
        user.save()
        TelegramProfile.objects.create(user=user, chat_id=chat_id)
    return user


def send_telegram_message(chat_id, text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return False

    try:
        res = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except requests.RequestException:
        logger.exception("Telegram sendMessage error")
        return False

    if not res.ok:
        logger.warning("Telegram sendMessage failed: %s", res.status_code)
    return res.ok
