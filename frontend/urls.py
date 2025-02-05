
from django.contrib import admin
from django.urls import path, include

from .views import EmployeeListView

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('filter', views.filter, name='filter'),

    path('report_branch', views.report_branch, name='report_branch'),
    path('report_employees', views.report_employees, name='report_employees'),

    path('all_employees/', EmployeeListView.as_view(), name='all_employees'),

    path('import/', views.import_data, name='import'),

    path('config/', views.config, name='config'),
]
