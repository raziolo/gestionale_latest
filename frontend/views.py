import json
from datetime import datetime
from pprint import pprint

from django.shortcuts import render, reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpRequest
from openpyxl import load_workbook
from io import BytesIO

from api.models import Import

from api.models import Branch

from api import formulas as f


# Create your views here.
def dashboard(request):

    return render(request, template_name="frontend/dashboard.html")




from django_tables2 import SingleTableView
from django_filters.views import FilterView

from .tables import EmployeeTable
from .filters import EmployeeFilter
from api.models import Employee

class EmployeeListView(FilterView, SingleTableView):
    model = Employee
    table_class = EmployeeTable
    template_name = "frontend/employees/all_employees.html"
    filterset_class = EmployeeFilter

    def get_queryset(self):
        return Employee.objects.all()


def import_data(request):
    if request.method == "GET":
        return render(request, "frontend/import/import.html")
    if request.method == "POST":
        # Get the uploaded file
        uploaded_file = request.FILES.get('file')
        selected_branch = request.POST.get('branchSelect')

        try:
            selected_branch = int(selected_branch)
        except:
            return JsonResponse({"status": "error", "errors": ["Internal"]}, status=200)

        if not selected_branch:
            return JsonResponse({"status": "error", "errors": ["no branch selected"]}, status=200)

        data_dict = dict

        branch_obj = Branch.objects.get(id=selected_branch)

        if branch_obj.get_brand() == "equivalenza":
            print("equivalenza")

            ### START CONVERTING DATA

            if uploaded_file:
                # Read the file as binary
                file_content = uploaded_file.read()

                # Load the workbook from the binary data
                workbook = load_workbook(filename=BytesIO(file_content))
                sheet = workbook.active  # You can specify sheet name if needed

                # Initialize the dictionary to hold the data
                data_dict = {}

                # Iterate through the rows, skipping the header
                for row in sheet.iter_rows(min_row=2, values_only=True):  # Skip the header row
                    date = row[1]  # assuming the date is in the second column
                    record = {
                        "Dipendente": row[0],
                        "Qta. Vend.": row[2],
                        "Sco.": row[3],
                        "Importo": row[4],
                        "Sco. Medio": row[5],
                        "Qta Media": row[6]
                    }

                    # If the date is already a key, append the new record to its list
                    if date in data_dict:
                        data_dict[date].append(record)
                    else:
                        # Otherwise, create a new list with the record
                        data_dict[date] = [record]

                import_qs = Import.objects.none()

                errors = []

                for date, records in data_dict.items():
                    employees_day_id_list = []

                    for record in records:
                        try:
                            employees_day_id_list.append(record['Dipendente'])
                        except:
                            errors.append(f"Employee {record['Dipendente']} not found")
                            continue

                    employees_day_qs = Employee.objects.filter(id__in=employees_day_id_list)

                    if employees_day_qs.count() != len(employees_day_id_list):
                        errors.append(f"Employees on {date} not found")
                        continue

                    branch_check_value = list(employees_day_qs.values_list('branch', flat=True))
                    normalized = list(dict.fromkeys(branch_check_value))
                    if len(normalized) != 1:
                        errors.append(f"Branch on {date} from different branch")
                        continue

                    if normalized[0] != selected_branch:
                        errors.append(f"Branch on {date} from different branch")
                        continue

                    if Import.objects.filter(branch=branch_obj, import_date=date):
                        errors.append(f"Collision on {date}")
                        continue

                if errors:
                    return JsonResponse({"status": "error", "errors": errors}, status=200)

                import_bulk_create_list = []
                for date, data in data_dict.items():
                    date_obj = datetime.strptime(date, '%d/%m/%Y')
                    date_str = date_obj.strftime('%Y-%m-%d')
                    i = Import(import_date=date_str, data=data, branch=branch_obj)
                    import_bulk_create_list.append(i)

                Import.objects.bulk_create(import_bulk_create_list)


            return JsonResponse({"status" : "success", "errors": []}, status=200)


def filter(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        filter_type = data.get('type')
        branch = data.get('branch')
        date = data.get('date')
        print(filter_type, branch, date)  # Should now print your values

        redirect_url = ""
        if filter_type == "branch":

            redirect_url = "/report_branch?branch={}&date={}".format(branch, date)

        elif filter_type == "employees":

            redirect_url = "/report_employees?branch={}&date={}".format(branch, date)

        return JsonResponse({"redirect_url": redirect_url})

def report_branch(request):
    if request.method == 'GET':
        # Get the query string parameters
        branch_param = request.GET.get('branch')
        date_param = request.GET.get('date')

        # Validate branch parameter
        if not branch_param:
            return JsonResponse({"status": "error", "errors": ["No branch selected"]}, status=400)
        try:
            branch_id = int(branch_param)
        except ValueError:
            return JsonResponse({"status": "error", "errors": ["Invalid branch ID"]}, status=400)

        # Convert the date parameter to string (it may be None)
        date = str(date_param) if date_param else ""

        # Initialize date_start and date_end
        date_start, date_end = None, None

        # Check if the date string contains a range (using "to")
        if "to" in date:
            parts = date.split("to")
            if len(parts) >= 2:
                date_start = parts[0].strip()
                date_end = parts[1].strip()
            else:
                date_start = date.strip()
                date_end = date.strip()
        else:
            # If no range is provided, you could either treat it as a single date or return an error.
            # Here, we treat it as a single date.
            date_start = date.strip()
            date_end = date.strip()

        # Generate the report (adjust parameters as needed)
        sc = f.generate_branch_report_scontrini(branch_id, date_start, date_end)
        branch = Branch.objects.get(id=branch_id)

        sales = f.generate_branch_report_sales(branch_id, date_start, date_end)

        context = {
            "sc": sc,
            "date_start": date_start,
            "branch": branch,
            "date_end": date_end,
            "sales": sales,
        }

        return render(request, "frontend/report/sede.html", context)

    # Optionally handle non-GET requests
    return JsonResponse({"status": "error", "errors": ["Invalid request method"]}, status=405)



def report_employees(request):
    if request.method == 'GET':
        # Get the query string parameters
        branch_param = request.GET.get('branch')
        date_param = request.GET.get('date')

        # Validate branch parameter
        if not branch_param:
            return JsonResponse({"status": "error", "errors": ["No branch selected"]}, status=400)
        try:
            branch_id = int(branch_param)
        except ValueError:
            return JsonResponse({"status": "error", "errors": ["Invalid branch ID"]}, status=400)

        # Convert the date parameter to string (it may be None)
        date = str(date_param) if date_param else ""

        # Initialize date_start and date_end
        date_start, date_end = None, None

        # Check if the date string contains a range (using "to")
        if "to" in date:
            parts = date.split("to")
            if len(parts) >= 2:
                date_start = parts[0].strip()
                date_end = parts[1].strip()
            else:
                date_start = date.strip()
                date_end = date.strip()
        else:
            # If no range is provided, you could either treat it as a single date or return an error.
            # Here, we treat it as a single date.
            date_start = date.strip()
            date_end = date.strip()

        # Generate the report (adjust parameters as needed)

        sc_performance = f.generate_report_performance_scontrini(branch_id, date_start, date_end)

        sales_performance = f.generate_report_performance_sales(branch_id, date_start, date_end)
        print(sales_performance)
        context = {
            "sc_performance": sc_performance,
            "branch": Branch.objects.get(id=branch_id),
            "date_start": date_start,
            "date_end": date_end,
            "sales_performance": sales_performance
        }

        return render(request, "frontend/report/employees.html", context)