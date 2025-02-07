
from django.contrib import admin
from django.urls import path, include

from .views import EmployeeListView

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('filter', views.filter, name='filter'),

    path('report_branch', views.report_branch, name='report_branch'),
    path('report_employees', views.report_employees, name='report_employees'),
    path('report_counter', views.report_counter, name='report_counter'),

    path('all_employees/', EmployeeListView.as_view(), name='all_employees'),
    path('new_employee/', views.new_employee, name='new_employee'),

    path('import/', views.import_data, name='import'),
    path('import/history/', views.import_history, name='import_history'),

    path('config/', views.config, name='config'),
]
