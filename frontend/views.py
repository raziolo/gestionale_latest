import json
from datetime import datetime, timedelta
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

from .tables import EmployeeTable, EmployeePerformancesTable
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

        elif branch_obj.get_brand() == "original":
            print("original")

            ### START CONVERTING DATA

            if uploaded_file:
                # Read the file as binary
                file_content = uploaded_file.read()

                # Load the workbook from the binary data
                workbook = load_workbook(filename=BytesIO(file_content))
                sheet = workbook.active  # You can specify sheet name if needed

                # Initialize the dictionary to hold the data
                data_dict = {}

                errors = []

                total_rows = sheet.max_row

                # Iterate through the rows, skipping the header
                for row in sheet.iter_rows(min_row=2, values_only=True):  # Skip the header row

                    if row[1] in ["Totale generale", "Totali "]:
                        continue


                    date = row[1]  # assuming the date is in the second column
                    record = {
                        "Qta. Vend.": row[2],
                        "Sco.": row[3],
                        "Importo": row[4],
                        "Sco. Medio": row[5],
                        "Qta Media": row[6]
                    }
                    if Import.objects.filter(branch=branch_obj, import_date=date):
                        errors.append(f"Collision on {date}")
                        continue

                    data_dict[date] = [record]

                import_qs = Import.objects.none()

                if errors:
                    return JsonResponse({"status": "error", "errors": errors}, status=200)

                data_dict_formatted = {}

                data_dict = {k: v for k, v in data_dict.items() if k is not None}

                for k,v in data_dict.items():

                    unformatted = k
                    date_strp = datetime.strptime(unformatted, '%d/%m/%Y')
                    date_str = date_strp.strftime('%Y-%m-%d')
                    data_dict_formatted[date_str] = v

                import_bulk_create_list = []
                for date, data in data_dict_formatted.items():
                    i = Import(import_date=date, data=data, branch=branch_obj)
                    import_bulk_create_list.append(i)

                Import.objects.bulk_create(import_bulk_create_list)



            return JsonResponse({"status": "success", "errors": []}, status=200)



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
        sc_total = int(sum(sc.values())) ## TOTALE SCONTRINI


        branch = Branch.objects.get(id=branch_id)

        sales = f.generate_branch_report_sales(branch_id, date_start, date_end)
        sales_total = sum(sales.values())
        sales_total = round(sales_total, 2)

        zoom_enabled = "false"
        graph_type = "area"

        if len(sales) > 30:
            zoom_enabled = "true"
            graph_type = "area"



        context = {
            "sc": sc,
            "sc_total": sc_total,
            "sales_total": sales_total,
            "brand": branch.get_brand(),
            "date_start": date_start,
            "branch": branch,
            "date_end": date_end,
            "sales": sales,
            "zoom_enabled": zoom_enabled,
            "type" : graph_type,
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

        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            return JsonResponse({"status": "error", "errors": ["Branch not found"]}, status=400)

        if branch.get_brand() == "original":
            return JsonResponse({"status": "error", "errors": ["Original Marines No Employee Performances"]}, status=400)

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


        medium_sc_sales = f.generate_medium_sc_sales(sc_performance)

        medium_sales_performance = f.generate_medium_sales_performance(sales_performance)

        medium_number_sales_performance = f.generate_medium_sales(sales_performance)

        performance_table_data = []

        for key, value in sc_performance.items():
            performance_table_data.append({
                    "employee": key,
                    "quantita": int(medium_number_sales_performance[key]),
                    "n_scontrini": medium_sc_sales[key],
                    "importo": medium_sales_performance[key],
                }
            )

        performances_table = EmployeePerformancesTable(performance_table_data, orderable=False)

        zoom_enabled = "true"
        graph_type = "area"

        if date_start == date_end:
            zoom_enabled = "false"
            graph_type = "bar"

        total_sales = sum([sum(sales) for sales in sales_performance.values()])
        total_sc = sum([sum(sc) for sc in sc_performance.values()])

        # Calculate the percentage for each employee within each KPI
        sales_percentage = {key: round((sum(sales) / total_sales) * 100, 2) if total_sales != 0 else 0
                            for key, sales in sales_performance.items()}
        sc_percentage = {key: round((sum(sc) / total_sc) * 100, 2) if total_sc != 0 else 0
                         for key, sc in sc_performance.items()}


        context = {
            "sc_performance": sc_performance,
            "branch": Branch.objects.get(id=branch_id),
            "date_start": date_start,
            "date_end": date_end,
            "sales_performance": sales_performance,
            "performances_table": performances_table,
            "sales_percentage": sales_percentage,
            "sc_percentage": sc_percentage,
            "zoom_enabled": zoom_enabled,
            "type" : graph_type,
        }

        return render(request, "frontend/report/employees.html", context)


def config(request):
    if request.method == 'GET':
        return render(request, "frontend/base_cms/config.html")


def import_history(request):
    from datetime import timedelta, datetime

    if request.method == 'GET':
        current_year = datetime.now().year
        years_list = range(current_year, current_year - 10, -1)

        return render(request, "frontend/import/history.html", {
            'years_list': years_list,
            'year': current_year,
        })

    elif request.method == 'POST':
        form_data = request.POST

        branch_id = form_data.get('branchSelect')
        year = form_data.get('year')

        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Branch not found'})

        try:
            m_year = int(year)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid year'})

        imports_objs_qs = Import.objects.filter(branch=branch)
        imports_objs_qs_filtered = Import.objects.none()

        # Filter for all import_obj containing the requested year
        for import_obj in imports_objs_qs:
            if import_obj.import_date.__contains__(year):
                imports_objs_qs_filtered |= Import.objects.filter(import_date=import_obj.import_date)

        # Build dictionary of all days in the selected year
        start_date = datetime(int(year), 1, 1)
        end_date = datetime(int(year), 12, 31)
        all_days_in_year = [
            (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            for i in range((end_date - start_date).days + 1)
        ]

        imports_report_mapped = {}

        # Mark days with import as 1
        for import_obj in imports_objs_qs_filtered:
            imports_report_mapped[import_obj.import_date] = 1
            if import_obj.import_date in all_days_in_year:
                all_days_in_year.remove(import_obj.import_date)

        # Remaining days get 0 for no import
        for day in all_days_in_year:
            imports_report_mapped[day] = 0

        # Now mark FUTURE days as -1
        today_str = datetime.now().strftime('%Y-%m-%d')
        today_date = datetime.strptime(today_str, '%Y-%m-%d').date()

        for day_str in imports_report_mapped.keys():
            day_date = datetime.strptime(day_str, '%Y-%m-%d').date()
            if day_date > today_date:
                imports_report_mapped[day_str] = -1

        # Sort dictionary by date
        imports_report_mapped = dict(sorted(imports_report_mapped.items()))

        # Rebuild years_list for re-render
        current_year = datetime.now().year
        years_list = range(current_year, current_year - 10, -1)

        context = {
            'imports': imports_report_mapped,
            'branch': branch,
            'years_list': years_list,
            'year': year,
        }

        return render(request, "frontend/import/history.html", context=context)


from django.shortcuts import render, redirect
from .forms import EmployeeForm


def new_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('all_employees')  # Change this to whatever view or URL you want
    else:
        form = EmployeeForm()

    return render(request, 'frontend/employees/new_employee.html', {'form': form})

