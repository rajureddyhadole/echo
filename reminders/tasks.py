import os

import requests
from celery import shared_task
from django.utils import timezone

from .models import Reminder


@shared_task
def check_due_reminders():
    now = timezone.now()

    due_reminders = Reminder.objects.filter(is_notified=False, remind_at__lte=now)

    count = 0
    for reminder in due_reminders:
        send_telegram_reminder.delay(reminder.id)
        # print(
        #     f"[CELERY NOTIFICATION] Reminder due for user {reminder.user}: {reminder.title}"
        # )
        count += 1

    return f"Processed {count} due reminders."


@shared_task
def send_telegram_reminder(reminder_id, chat_id=None):
    try:
        reminder = Reminder.objects.get(id=reminder_id)

        token = os.getenv("TELEGRAM_BOT_TOKEN")
        target_chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

        if not target_chat_id:
            print("[TELEGRAM ERROR] No valid chat_id provided.")
            return "Failed: No chat_id provided."

        message = (
            f"🔔 Reminder: {reminder.title}\n(Scheduled for: {reminder.remind_at})"
        )

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": target_chat_id,
            "text": message,
        }

        response = requests.post(url, json=payload)
        print(
            f"[TELEGRAM API] Status: {response.status_code} | Response: {response.text}"
        )

        if response.status_code == 200:
            reminder.is_notified = True
            reminder.save()
            return f"Successfully sent Telegram notification for: {reminder.title}"
        else:
            return f"Failed to send Telegram message: {response.text}"

    except Reminder.DoesNotExist:
        return "Reminder not found."
