from django.contrib import admin

from .models import Reminder

# Register your models here.


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "title",
        "description",
        "remind_at",
        "is_notified",
        "created_at",
    ]
    list_filter = ["user", "is_notified", "created_at"]
