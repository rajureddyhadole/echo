from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

# Create your tests here.

User = get_user_model()


class AccountsTests(APITestCase):
    def setUp(self):
        self.register_url = reverse("register")
        self.token_url = reverse("token_obtain_pair")

        self.user_data = {
            "email": "testuser@gmail.com",
            "password": "securepassword123",
            "first_name": "test",
            "last_name": "user",
        }

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(User.objects.count(), 1)

        self.assertEqual(User.objects.get().email, "testuser@gmail.com")

        self.assertNotIn("password", response.data)

    def test_user_login_jwt(self):
        User.objects.create_user(
            email="loginuser@example.com", password="mypassword123"
        )

        login_data = {
            "email": "loginuser@example.com",
            "password": "mypassword123",
        }

        response = self.client.post(self.token_url, login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_user_login_invalid_credentials(self):
        User.objects.create_user(
            email="loginuser@example.com",
            password="mypassword123",
        )

        login_data = {
            "email": "loginuser@example.com",
            "password": "wrongpassword123",
        }

        response = self.client.post(self.token_url, login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
