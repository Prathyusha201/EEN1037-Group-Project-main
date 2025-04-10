from django.contrib.auth.models import AbstractUser
from django.db import models

# Custom User Model
class User(AbstractUser):
    ROLE_CHOICES = [
        ('Technician', 'Technician'),
        ('Repair', 'Repair'),
        ('Manager', 'Manager'),
        ('View-only', 'View-only')
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

# Machine Model
class Machine(models.Model):
    STATUS_CHOICES = [
        ('OK', 'OK'),
        ('Warning', 'Warning'),
        ('Fault', 'Fault')
    ]
    name = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name + "(SN: " + self.serial_number + ")"

# Case Model
class Case(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed')
    ]
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name="cases")
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# Case Updates Model
class CaseUpdate(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="updates")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    update_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# Collection Model
class Collection(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

# Machine Collection Association
class MachineCollection(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)

# Report Model
class Report(models.Model):
    report_type = models.CharField(max_length=50)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    report_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

# API Logs Model
class APILog(models.Model):
    request_data = models.JSONField()
    response_data = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
