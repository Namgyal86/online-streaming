# custom_admin/urls.py
from django.urls import path
from .views import adminDashboard

urlpatterns = [
    path('admin-dashboard/', adminDashboard, name='admin_dashboard'),
]
