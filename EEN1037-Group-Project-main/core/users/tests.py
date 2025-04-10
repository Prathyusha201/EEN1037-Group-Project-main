from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class UserAuthenticationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')

    def test_login_valid_user(self):
        response = self.client.post('/users/login/', {'username': 'test@example.com', 'password': 'testpass123'})
        self.assertEqual(response.status_code, 200)

    def test_login_invalid_user(self):
        response = self.client.post('/users/login/', {'username': 'invalid@example.com', 'password': 'wrongpass'})
        self.assertEqual(response.status_code, 401)