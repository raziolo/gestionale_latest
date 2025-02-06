# tables.py
import django_tables2 as tables
from api.models import Employee

class EmployeeTable(tables.Table):
    class Meta:
        model = Employee
        template_name = "django_tables2/bootstrap.html"  # You can customize the template
        fields = ("id" ,"first_name", "last_name", "branch", "role")


class EmployeePerformancesTable(tables.Table):
    employee = tables.Column(
        verbose_name="Dipendente",
        attrs={"th": {"class": "text-left text-xl"}, "td": {"class": "font-bold text-left"}}
    )
    quantita = tables.Column(
        verbose_name="Quantità",
        attrs={"th": {"class": "text-right text-xl"}, "td": {"class": "text-right"}}
    )
    n_scontrini = tables.Column(
        verbose_name="N. Scontrini",
        attrs={"th": {"class": "text-right text-xl"}, "td": {"class": "text-right"}}
    )
    importo = tables.Column(
        verbose_name="Importo",
        attrs={"th": {"class": "text-right text-xl"}, "td": {"class": "text-right"}}
    )

    class Meta:
        template_name = "django_tables2/bootstrap.html"
        attrs = {
            "class": "table table-striped table-hover w-full text-lg",
        }
