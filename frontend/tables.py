# tables.py
import django_tables2 as tables
from api.models import Employee

class EmployeeTable(tables.Table):
    class Meta:
        model = Employee
        template_name = "django_tables2/bootstrap.html"  # You can customize the template
        fields = ("id" ,"first_name", "last_name", "branch", "role")


class EmployeePerformancesTable(tables.Table):
    # Define columns with names matching your dictionary keys.
    # (You can change the keys in your dictionaries or the column names as needed.)
    employee = tables.Column(verbose_name="Dipendente")
    quantita = tables.Column(verbose_name="Quantita'")
    n_scontrini = tables.Column(verbose_name="N. Scontrini")
    importo = tables.Column(verbose_name="Importo")

    class Meta:
        template_name = "django_tables2/bootstrap.html"