from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .agents.agent import run_companion_agent
from .models import ChatMessage
from .pagination import ChatPagination
from .serializers import ChatHistoryResponseSerializer, ChatSerializer

# Create your views here.


class ChatView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data["message"]
        user_identifier = request.user.id

        ai_response = run_companion_agent(message, user_identifier)

        ChatMessage.objects.create(
            user=user_identifier,
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
