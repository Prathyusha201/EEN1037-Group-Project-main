"""
URL configuration for acme_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from rest_framework import routers

from acme_backend.views import *

urlpatterns = [
    path('', include('core.urls')), 
    
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("api/machines/", MachineList.as_view(), name="machine-list"),
    path("api/machines/<int:pk>/", MachineDetail.as_view(), name="machine-detail"),
    path("api/cases/", CaseList.as_view(), name="case-list"),
    path("api/cases/open", CaseOpenList.as_view(), name="case-open-list"),
    path("api/cases/<int:pk>/", CaseDetail.as_view(), name="case-detail"),
    path("api/cases/<int:pk>/updates", CaseUpdateCreate.as_view(), name="case-updates"),
    path("api/caseupdate/<int:pk>/", CaseUpdateDetail.as_view(), name="caseupdate-detail"),
    path('api/', api_root), # api root

]
