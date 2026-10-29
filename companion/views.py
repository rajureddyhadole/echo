import time

from django.conf import settings
from groq import Groq
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatMessage
from .serializers import ChatSerializer

# Create your views here.


class ChatView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data["message"]

        try:
            client = Groq(api_key=settings.GROQ_API_KEY)

            system_prompt = """You are Echo, a helpful, concise AI companion.
            Keep your replies short, direct, and conversational (1-3 sentences).
            unless the user explicitly asks you to elaborate or explain deeply."""

            start = time.time()
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
                model="openai/gpt-oss-20b",
            )

            reply = chat_completion.choices[0].message.content

            print("Gemini took:", time.time() - start, "seconds")

            chat_record = ChatMessage.objects.create(
                user=request.user,
                user_message=message,
                ai_response=reply,
            )

            return Response(
                {
                    "id": chat_record.id,
                    "message": chat_record.user_message,
                    "reply": chat_record.ai_response,
                    "created_at": chat_record.created_at,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as err:
            print(f"Gemini api error, {err}")

            return Response(
                {"error": "unable to generate response. try again later"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
