from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .agents.agent import run_companion_agent
from .serializers import ChatSerializer

# Create your views here.


class ChatView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data["message"]
        user_identifier = str(request.user.id)

        ai_response = run_companion_agent(message, user_identifier)

        return Response({"response": ai_response})
