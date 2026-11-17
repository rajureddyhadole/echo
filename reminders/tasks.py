import logging

from celery import shared_task
from django.utils import timezone

from companion.telegram_utils import send_telegram_message

from .models import Reminder

logger = logging.getLogger(__name__)


@shared_task
def check_due_reminders():
    now = timezone.now()
    due_ids = Reminder.objects.filter(
        is_notified=False, remind_at__lte=now
    ).values_list("id", flat=True)

    count = 0
    for reminder_id in due_ids:
        send_telegram_reminder.delay(reminder_id)
        count += 1

    return f"Processed {count} due reminders."


@shared_task
def send_telegram_reminder(reminder_id):
    try:
        reminder = Reminder.objects.select_related("user__telegram").get(id=reminder_id)
    except Reminder.DoesNotExist:
        return "Reminder not found."

    profile = getattr(reminder.user, "telegram", None)
    if profile is None:
        logger.warning("User %s has no Telegram profile", reminder.user_id)
        return "Failed: user has no linked chat."

    claimed = Reminder.objects.filter(id=reminder_id, is_notified=False).update(
        is_notified=True
    )

    if not claimed:
        return "Already sent or in progress."

    local_time = timezone.localtime(reminder.remind_at).strftime("%d %b %Y, %I:%M %p")
    text = f"🔔 Reminder: {reminder.title}\n(Scheduled for: {local_time})"

    if send_telegram_message(profile.chat_id, text):
        return f"Sent: {reminder.title}"

    Reminder.objects.filter(id=reminder_id).update(is_notified=False)
    return "Failed to send."
