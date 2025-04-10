from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import *

from rest_framework.test import force_authenticate
from rest_framework.test import APIClient

class CaseUpdatesTest(APITestCase):

    def setUp(self):
        # Creating objects
        Machine.objects.create(name="Machine 1", serial_number="SN1", status="OK")
        Case.objects.create(machine=Machine.objects.get(serial_number="SN1"), status="", description="Case1")
        
        # Login
        self.user = User.objects.create_user(username='test', password='test')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)


    def test_create_case_update(self):
        """
        Ensure we can create a new case-update object when logged in.
        """
        url = reverse('case-updates', kwargs={'pk': Case.objects.get().pk})
        text = "My case update text"
        data = {'update_text': text}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CaseUpdate.objects.filter().count(), 1)
        self.assertEqual(CaseUpdate.objects.get().update_text, text)
        self.assertEqual(CaseUpdate.objects.get().updated_by, self.user)


class MachineStatusTest(APITestCase):

    def setUp(self):
        # Creating objects
        self.machine = Machine.objects.create(name="Machine 1", serial_number="SN1", status="OK")
        
        # Login
        self.user = User.objects.create_user(username='test', password='test')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_machine_status_get(self):
        """
        Ensure we can get details on a machine (includes its status)
        """
        url = reverse('machine-detail', kwargs={'pk': self.machine.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], "OK")

        self.machine.status = "Warning"
        self.machine.save()
        url = reverse('machine-detail', kwargs={'pk': self.machine.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], "Warning")

    def test_machine_status_set(self):
        """
        Ensure we can update a machine's status with a patch request
        """
        m = Machine.objects.get()
        url = reverse('machine-detail', kwargs={'pk': m.pk})
        data = {"status": "Warning"}
        response = self.client.patch(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CaseTest(APITestCase):
    
    def setUp(self):
        self.machine = Machine.objects.create(name="Machine 1", serial_number="SN1", status="OK")
        # Login
        self.user = User.objects.create_user(username='test', password='test')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_case_creation(self):
        """
        Ensure we can create a new failure/warning case
        """
        desc_txt = "Power supply dead"
        data = {
            "machine": Machine.objects.get().pk,
            "status": "Open",
            "description": desc_txt,
        }

        url = reverse("case-list")
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Case.objects.all().count(), 1)
        self.assertEqual(Case.objects.get().description, desc_txt)
        self.assertEqual(Case.objects.get().status, "Open")