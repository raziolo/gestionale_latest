# tables.py
import django_tables2 as tables
from api.models import Employee
from django.utils.html import format_html

class EmployeeTable(tables.Table):
    class Meta:
        model = Employee
        template_name = "django_tables2/bootstrap.html"  # You can customize the template
        fields = ("id" ,"first_name", "last_name", "branch", "role")


class EmployeePerformancesTable(tables.Table):
    employee = tables.Column(
        verbose_name="Dipendente",
        attrs={"th": {"class": "text-left text-xl text-info"}, "td": {"class": "font-bold text-left text-xl"}}
    )

    quantita = tables.Column(
        verbose_name="Quantità",
        attrs={"th": {"class": "text-right text-xl text-info"}, "td": {"class": "text-right text-xl"}},
        accessor="quantita",  # Assuming this field is available in your model
    )

    n_scontrini = tables.Column(
        verbose_name="N. Scontrini",
        attrs={"th": {"class": "text-right text-xl text-info"}, "td": {"class": "text-right text-xl"}},
        accessor="n_scontrini",  # Assuming this field is available in your model
    )

    importo = tables.Column(
        verbose_name="Importo",
        attrs={"th": {"class": "text-right text-xl text-info"}, "td": {"class": "text-right text-xl"}},
        accessor="importo",  # Assuming this field is available in your model
    )

    def render_quantita(self, value):
        return format_html('<span class="badge bg-base-100 badge-primary p-3 m-3 text-info" style="font-size: 1.5rem;">{}</span>', value)

    def render_n_scontrini(self, value):
        return format_html('<span class="badge bg-base-100 badge-primary p-3 m-3 text-info" style="font-size: 1.5rem;">{}</span>', value)

    def render_importo(self, value):
        return format_html('€<span class="badge bg-base-100 badge-primary p-3 m-3 text-info" style="font-size: 1.5rem;">{}</span>', value)

    class Meta:
        template_name = "django_tables2/bootstrap.html"
        attrs = {
            "class": "table table-zebra table-hover table-compact w-full text-lg",
        }

