from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # Password Management
    path('password/reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/reset/complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('password/change/', views.change_password, name='change_password'),
    
    # User Management (admin only)
    path('list/', views.UserListView.as_view(), name='user_list'),
    path('create/', views.UserCreateView.as_view(), name='user_create'),
    path('update/<int:pk>/', views.UserUpdateView.as_view(), name='user_update'),
    
    # User Profile
    path('profile/', views.profile_view, name='profile'),
    
    # API Endpoints for user management
    path('api/search/', views.search_users, name='search_users'),
    path('api/toggle-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    
    # Machine assignments
    path('assignments/', views.user_machine_assignments, name='user_machine_assignments'),
    path('assignments/add/', views.add_user_machine_assignment, name='add_user_machine_assignment'),
    path('assignments/remove/<int:assignment_id>/', views.remove_user_machine_assignment, name='remove_user_machine_assignment'),
]