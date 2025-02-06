import django_filters
from api.models import Employee, Branch, Role
from django import forms
from django.db.models import Q



class EmployeeFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method='filter_common_search',
        label="Cerca",  # Translatable label
        widget=forms.TextInput(attrs={
            "class": "input input-bordered",
            "placeholder": "Cerca..."  # Translatable placeholder
        })
    )
    branch = django_filters.ModelChoiceFilter(
        queryset=Branch.objects.all(),
        empty_label="Tutte",  # Translatable empty label
        label="Sede",
        widget=forms.Select(attrs={
            "class": "select select-bordered",
            'placeholder': "Tutte"
        })
    )
    role = django_filters.ModelChoiceFilter(
        queryset=Role.objects.all(),
        empty_label="Tutti",  # Translatable empty label
        label="Ruolo",
        widget=forms.Select(attrs={
            "class": "select select-bordered",
            'placeholder': "Tutti"

        })
    )

    class Meta:
        model = Employee
        fields = ['search', 'branch', 'role']

    def filter_common_search(self, queryset, name, value):
        # Custom search logic
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(branch__name__icontains=value) |
            Q(role__name__icontains=value)
        )