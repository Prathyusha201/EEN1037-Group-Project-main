from django.contrib.auth.models import Group, User
from rest_framework import serializers

from core.models import *

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'role']
        read_only_fields = ['id', 'role']

class MachineSerializer(serializers.HyperlinkedModelSerializer):
    assigned_to = serializers.StringRelatedField(read_only=True)
    cases = serializers.HyperlinkedRelatedField(many=True, queryset=Case.objects.all(), view_name="case-detail")
    class Meta:
        model = Machine
        fields = ['id', 'url',  'name', 'serial_number', 'status', 'assigned_to', 'created_at', 'cases']
        read_only_fields = ['id', 'name', 'created_at', 'serial_number', 'assigned_to', 'created_at', 'cases']


class CaseUpdateSerializer_W(serializers.HyperlinkedModelSerializer):
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    updated_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    class Meta:
        model = CaseUpdate
        fields = ['case', 'updated_by', 'update_text', 'created_at']

class CaseUpdateSerializer_L(serializers.HyperlinkedModelSerializer):
    case = serializers.HyperlinkedRelatedField(read_only=True, view_name="case-detail")
    updated_by = serializers.StringRelatedField()
    class Meta:
        model = CaseUpdate
        fields = ['case', 'updated_by', 'update_text']

class CaseSerializer(serializers.HyperlinkedModelSerializer):
    reported_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    machine = serializers.PrimaryKeyRelatedField(queryset=Machine.objects.all())
    class Meta:
        model = Case
        fields = ['id', 'machine', 'reported_by', 'status', 'description', 'created_at', 'updated_at']


class CollectionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Collection
        fields = ['collection', 'machine']

class ReportSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Report
        fields = ['report_type', 'generated_by', 'report_data', 'created_at']


class APILogSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = APILog
        fields = ['request_data', 'response_data', 'timestamp']
        
