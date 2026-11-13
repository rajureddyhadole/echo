import json
import os

import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .agents.agent import run_companion_agent
from .models import ChatMessage
from .pagination import ChatPagination
from .serializers import ChatHistoryResponseSerializer, ChatSerializer

# Create your views here.
load_dotenv()


class ChatView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data["message"]
        user_identifier = request.user.id

        ai_response = run_companion_agent(message, user_identifier)

        ChatMessage.objects.create(
            user_id=user_identifier,
            user_message=message,
            ai_response=ai_response,
        )

        return Response({"response": ai_response})

    def get(self, request):
        chat_history = ChatMessage.objects.filter(user=request.user).order_by(
            "-created_at"
        )
        paginator = ChatPagination()

        paginated_chat_history = paginator.paginate_queryset(
            chat_history,
            request,
            view=self,
        )

        response_serializer = ChatHistoryResponseSerializer(
            paginated_chat_history, many=True
        )

        return paginator.get_paginated_response(response_serializer.data)


@csrf_exempt
def telegram_webhook_view(request):
    if request.method != "POST":
        return JsonResponse({"status": "only POST requests allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        if "message" not in data:
            return JsonResponse({"status": "ok"})

        message_data = data["message"]
        chat_id = message_data["chat"]["id"]
        user_message = message_data.get("text", "")

        if not user_message:
            return JsonResponse({"status": "ok"})

        user_id = message_data["from"]["id"]

        ai_response_text = run_companion_agent(
            user_message=user_message, user_id=user_id
        )

        token = os.getenv("TELEGRAM_BOT_TOKEN")

        if not token:
            print("[ERROR] TELEGRAM_BOT_TOKEN is None or empty!")
            return JsonResponse(
                {"status": "error", "message": "Bot token missing"}, status=500
            )

        telegram_url = f"https://api.telegram.org/bot{token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": ai_response_text,
        }

        # Log exact HTTP response from Telegram
        tg_res = requests.post(telegram_url, json=payload)
        print(f"[WEBHOOK OUTGOING] Status: {tg_res.status_code} | Body: {tg_res.text}")

        return JsonResponse({"status": "success"})

    except Exception as e:
        print(f"Error handling Telegram webhook: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
