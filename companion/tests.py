from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from companion.telegram_utils import get_or_create_telegram_user

from .models import TelegramProfile

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

    @patch("companion.views.run_companion_agent", return_value="Hi there!")
    def test_authenticated_user_can_chat(self, mock_agent):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)

        chat_payload = {"message": "hii, echo"}

        response = self.client.post(self.chat_url, chat_payload, format="json")

        self.assertIn("response", response.data)
        self.assertEqual(response.data["response"], "Hi there!")

    def test_unauthenticated_cannot_chat(self):

        self.client.credentials()

        chat_payload = {"message": "hello there"}

        response = self.client.post(self.chat_url, chat_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertNotIn("reply", response.data)


class GetOrCreateTelegramUserTests(TestCase):
    def test_creates_user_and_profile(self):
        user = get_or_create_telegram_user(555)

        self.assertEqual(user.email, "tg_555@telegram.local")
        self.assertEqual(user.telegram.chat_id, 555)

    def test_same_chat_id_returns_same_user(self):
        first = get_or_create_telegram_user(555)
        second = get_or_create_telegram_user(555)

        self.assertEqual(first.id, second.id)
        self.assertEqual(TelegramProfile.objects.filter(chat_id=555).count(), 1)
