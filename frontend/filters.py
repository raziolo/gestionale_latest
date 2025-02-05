import django_filters
from api.models import Employee, Branch, Role
from django import forms
from django.db.models import Q


from django.utils.translation import gettext_lazy as _  # Import for translation

class EmployeeFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method='filter_common_search',
        label=_("Cerca"),  # Translatable label
        widget=forms.TextInput(attrs={
            "class": "input input-bordered",
            "placeholder": _("Search employees...")  # Translatable placeholder
        })
    )
    branch = django_filters.ModelChoiceFilter(
        queryset=Branch.objects.all(),
        empty_label=_("Tutte"),  # Translatable empty label
        widget=forms.Select(attrs={
            "class": "select select-bordered",
            'placeholder': _("Tutte")
        })
    )
    role = django_filters.ModelChoiceFilter(
        queryset=Role.objects.all(),
        empty_label=_("All Roles"),  # Translatable empty label
        widget=forms.Select(attrs={
            "class": "select select-bordered",
            'placeholder': _("Tutti")

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