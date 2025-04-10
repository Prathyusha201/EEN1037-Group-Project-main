from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import permissions, generics, response, viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly

from core.models import Machine, User, Case
from acme_backend.serializers import *
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.settings import api_settings

# REST API
@api_view(["GET"])
@permission_classes((permissions.AllowAny,))
def api_root(request, format=None):
    return Response(
        {
            "machines": reverse("machine-list", request=request, format=format),
            "cases": reverse("case-list", request=request, format=format),
        }
    )

class MachineDetail(generics.RetrieveUpdateAPIView):
    """
    API endpoint that allows a machine to be viewed (get) and its status edited (patch only).
    """
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'patch']

class MachineList(generics.ListAPIView):
    """
    API endpoint that allows listing of all existing machines
    """
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class CaseDetail(generics.RetrieveUpdateAPIView):
    """
    API endpoint that allows a case to be viewed or edited.
    """
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def retrieve(self, request, *args, **kwargs):
        d = super().retrieve(request, *args, **kwargs)
        d.data["updates"] = reverse("case-updates", kwargs=kwargs, request=request)
        return d

class CaseUpdateDetail(generics.RetrieveAPIView):
    """
    API endpoint that allows a case update to be viewed.
    """
    queryset = CaseUpdate.objects.all().order_by("-created_at")
    serializer_class = CaseUpdateSerializer_L
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]



class CaseList(generics.ListCreateAPIView):
    """
    API endpoint that allows cases to be listed and created.
    """
    queryset = Case.objects.filter()
    serializer_class = CaseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        dC = request.data.copy()
        dC['reported_by'] = request.user.pk
        print(dC)
        serializer = self.get_serializer(data=dC)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class CaseOpenList(generics.ListAPIView):
    """
    API endpoint that allows cases to be listed and created.
    """
    queryset = Case.objects.filter(status="Open")
    serializer_class = CaseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class CaseUpdateCreate(generics.ListCreateAPIView):
    """
    API endpoint that allows cases to be listed and created.
    """
    queryset = CaseUpdate.objects.all()
    serializer_class = CaseUpdateSerializer_L
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'post']

    def create(self, request, *args, **kwargs):
        caseID = self.kwargs['pk']
        userID = request.user.pk
        request.data['case'] = caseID
        request.data['updated_by'] = userID
        
        # Using a different serializer when creating an object, so it only asks for the update_text and everything else is automatically populated
        serializer_class = CaseUpdateSerializer_W(data=request.data)
        serializer_class.is_valid(raise_exception=True)
        serializer_class.save()
        headers = {}
        try:    
            headers= {'Location': str(serializer_class.data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            pass
        return Response(serializer_class.data, status=status.HTTP_201_CREATED, headers=headers)

