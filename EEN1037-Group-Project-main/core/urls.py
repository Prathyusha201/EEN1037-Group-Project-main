from django.urls import path
from django.http import HttpResponse
from django.contrib import admin
from django.urls import path
from django.contrib.auth.views import LogoutView  # Import LogoutView

from . import views

# Simple function-based view for testing
def home(request):
    return HttpResponse("Hello, Django is working!")

urlpatterns = [
    path('', views.index, name="index"),
    path('admin/', admin.site.urls),

    # Core paths
    path('dashboard/', views.dashboard, name="dashboard"),
    path('machines/', views.machines, name="machines"),
    path('collections/', views.collections, name="collections"),
    path('cases/', views.cases, name="cases"),

    # Auth paths
    path('signin/', views.signin, name="sign-in"),
    path('reset-password/', views.resetPassword, name="reset-password"),
    path('static-pages/', views.static_pages, name="static-pages"),
    path('logout/', LogoutView.as_view(), name="logout"),

    # HTMX paths
    path('dashboard/section/<str:section>/', views.dashboard_section, name="dashboard_section"),
    path('machines/section/<str:section>/', views.machines_section, name="machines_section"),
    path('cases/section/<str:section>/', views.cases_section, name="cases_section"),
]
