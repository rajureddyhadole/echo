from django.conf import settings
from django.db import models


class Reminder(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reminders",
    )
    title = models.CharField(max_length=400)
    description = models.TextField(max_length=600, blank=True, null=True)
    remind_at = models.DateTimeField(db_index=True)
    is_notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.title} @ {self.remind_at}"
