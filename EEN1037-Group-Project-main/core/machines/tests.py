from django.test import TestCase
from users.models import User
from machines.models import Machine

class MachineStatusTest(TestCase):
    def setUp(self):
        self.technician = User.objects.create_user(username='tech', email='tech@example.com', password='test123', role='technician')
        self.repair = User.objects.create_user(username='repair', email='repair@example.com', password='test123', role='repair')
        self.machine = Machine.objects.create(name="CNC Machine", model_number="CNC-123", serial_number="SN001")

    def test_technician_can_set_warning(self):
        self.client.login(username='tech@example.com', password='test123')
        response = self.client.post(f'/machines/{self.machine.id}/set_status/', {'status': 'Warning'})
        self.assertEqual(response.status_code, 200)

    def test_repair_cannot_set_warning(self):
        self.client.login(username='repair@example.com', password='test123')
        response = self.client.post(f'/machines/{self.machine.id}/set_status/', {'status': 'Warning'})
        self.assertEqual(response.status_code, 403)