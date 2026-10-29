from django.contrib import admin

from .models import ChatMessage

# Register your models here.


@admin.register(ChatMessage)
class chatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "user_message_preview", "ai_response", "created_at")
    list_filter = ("created_at", "user")
    search_fields = ("user__email", "user_message", "ai_response")

    def user_message_preview(self, obj):
        return (
            obj.user_message[:50] + "..."
            if len(obj.user_message) > 50
            else obj.user_message
        )

    user_message_preview.short_description = "User Message"
