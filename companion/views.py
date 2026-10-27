import time

from django.conf import settings
from groq import Groq
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ChatSerializer

# Create your views here.


class ChatView(APIView):
    def post(self, request):
        serializer = ChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data["message"]

        try:
            client = Groq(api_key=settings.GROQ_API_KEY)

            start = time.time()
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": message,
                    }
                ],
                model="openai/gpt-oss-20b",
            )

            reply = chat_completion.choices[0].message.content
            print("Gemini took:", time.time() - start, "seconds")

            return Response({"message": message, "reply": reply})

        except Exception as err:
            print(f"Gemini api error, {err}")

            return Response(
                {"error": "unable to generate response. try again later"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
