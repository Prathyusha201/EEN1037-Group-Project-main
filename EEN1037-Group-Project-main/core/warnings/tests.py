from django.test import TestCase
from users.models import User
from machines.models import Machine
from warnings.models import Warning

class WarningSystemTest(TestCase):
    def setUp(self):
        self.tech = User.objects.create_user(username='tech', email='tech@example.com', password='test123', role='technician')
        self.machine = Machine.objects.create(name="Lathe", model_number="L-789", serial_number="L789")

    def test_duplicate_warning_not_allowed(self):
        self.client.login(username='tech@example.com', password='test123')
        Warning.objects.create(machine=self.machine, text="Overheating", is_active=True)
        response = self.client.post(f'/warnings/{self.machine.id}/add/', {'text': 'Overheating'})
        self.assertEqual(response.status_code, 400)