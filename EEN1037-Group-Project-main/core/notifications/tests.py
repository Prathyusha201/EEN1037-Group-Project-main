from django.test import TestCase
from users.models import User
from machines.models import Machine
from notifications.utils import send_notification

class NotificationTest(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username='manager', email='manager@example.com', password='test123', role='manager')

    def test_notification_sent(self):
        send_notification(self.manager, "Test Notification", "This is a test")
        self.assertEqual(self.manager.notifications.count(), 1)