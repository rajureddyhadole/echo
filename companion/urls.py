from django.urls import path

from .views import ChatView, telegram_webhook_view

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat_api"),
    path("webhook/telegram/", telegram_webhook_view, name="telegram_webhook"),
]
