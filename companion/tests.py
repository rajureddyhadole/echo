from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

# Create your tests here.

User = get_user_model()


class ChatAPITests(APITestCase):
    def setUp(self):
        User.objects.create_user(
            email="chatter@example.com", password="securepassword123"
        )

        self.chat_url = reverse("chat_api")
        self.token_url = reverse("token_obtain_pair")

        token_reponse = self.client.post(
            self.token_url,
            {
                "email": "chatter@example.com",
                "password": "securepassword123",
            },
            format="json",
        )

        self.access_token = token_reponse.data["access"]

    def test_authenticated_user_can_chat(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)

        chat_payload = {"message": "hii, echo"}

        response = self.client.post(self.chat_url, chat_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("reply", response.data)

    def test_unauthenticated_cannot_chat(self):

        self.client.credentials()

        chat_payload = {"message": "hello there"}

        response = self.client.post(self.chat_url, chat_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertNotIn("reply", response.data)
