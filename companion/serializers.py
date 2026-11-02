from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ChatMessage

User = get_user_model()


class ChatSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=4000, trim_whitespace=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name"]


class ChatHistoryResponseSerializer(serializers.ModelSerializer):
    user_info = UserSerializer(source="user", read_only=True)

    class Meta:
        model = ChatMessage
        fields = ["id", "user_message", "ai_response", "user_info", "created_at"]
