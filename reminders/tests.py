from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from companion.models import TelegramProfile

from .models import Reminder
from .tasks import send_telegram_reminder

# Create your tests here.


class SendTelegramReminderTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email="a@test.com")
        TelegramProfile.objects.create(user=self.user, chat_id=123)
        self.reminder = Reminder.objects.create(
            user=self.user, title="call mom", remind_at=timezone.now()
        )

    @patch("reminders.tasks.send_telegram_message", return_value=True)
    def test_success_marks_notified(self, mock_send):
        send_telegram_reminder(self.reminder.id)

        self.reminder.refresh_from_db()
        self.assertTrue(self.reminder.is_notified)
        self.assertEqual(mock_send.call_args[0][0], 123)

    @patch("reminders.tasks.send_telegram_message", return_value=False)
    def test_failure_keeps_reminder_unsent(self, mock_send):
        send_telegram_reminder(self.reminder.id)

        self.reminder.refresh_from_db()
        self.assertFalse(self.reminder.is_notified)
