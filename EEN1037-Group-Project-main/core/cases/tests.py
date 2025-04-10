from django.test import TestCase
from core.users.models import User
from machines.models import Machine
from cases.models import Case

class CaseManagementTest(TestCase):
    def setUp(self):
        self.tech = User.objects.create_user(username='tech', email='tech@example.com', password='test123', role='technician')
        self.machine = Machine.objects.create(name="Drill", model_number="D-456", serial_number="D456")
        self.case = Case.objects.create(machine=self.machine, created_by=self.tech, status="open")

    def test_case_creation(self):
        self.client.login(username='tech@example.com', password='test123')
        response = self.client.post(f'/cases/{self.machine.id}/create/', {'notes': 'Machine is broken'})
        self.assertEqual(response.status_code, 201)

    def test_repair_can_resolve_case(self):
        repair = User.objects.create_user(username='repair', email='repair@example.com', password='test123', role='repair')
        self.client.login(username='repair@example.com', password='test123')
        response = self.client.post(f'/cases/{self.case.id}/resolve/', {})
        self.assertEqual(response.status_code, 200)