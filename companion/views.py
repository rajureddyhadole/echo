import hmac
import json

from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .agents.agent import run_companion_agent
from .models import ChatMessage
from .pagination import ChatPagination
from .serializers import ChatHistoryResponseSerializer, ChatSerializer
from .tasks import process_telegram_message
from .telegram_utils import get_or_create_telegram_user, send_telegram_message

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

    secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", "")
    received = request.META.get("HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN", "")
    if not secret or not hmac.compare_digest(received, secret):
        return HttpResponseForbidden()

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"status": "ok"})

    message = data.get("message")
    if not message:
        return JsonResponse({"status": "ok"})

    chat_id = (message.get("chat") or {}).get("id")
    text = message.get("text", "")

    if not chat_id or not text:
        return JsonResponse({"status": "ok"})

    allowed = settings.ALLOWED_TELEGRAM_CHAT_IDS
    if allowed and chat_id not in allowed:
        return JsonResponse({"status": "ok"})

    user = get_or_create_telegram_user(chat_id)

    if text.strip().startswith("/start"):
        send_telegram_message(
            chat_id,
            "Hi, I'm Echo! I'm here to chat, listen, and remind you of things. "
            "How are you feeling today?",
        )

        return JsonResponse({"status": "ok"})

    process_telegram_message.delay(user.id, chat_id, text)
    return JsonResponse({"status": "ok"})
