import json
from datetime import datetime, timedelta
from pprint import pprint

from django.utils.datastructures import MultiValueDictKeyError

from django.shortcuts import render, reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpRequest
from openpyxl import load_workbook
from io import BytesIO

from api.models import Import, Schedule

from api.models import Branch

from api import formulas as f


# Create your views here.
def dashboard(request):

    return render(request, template_name="frontend/dashboard.html")




from django_tables2 import SingleTableView
from django_filters.views import FilterView

from .tables import EmployeeTable, EmployeePerformancesTable, SchedulesTable
from .filters import EmployeeFilter
from api.models import Employee

class EmployeeListView(FilterView, SingleTableView):
    model = Employee
    table_class = EmployeeTable
    template_name = "frontend/employees/all.html"
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
        selected_type = request.POST.get('typeSelect')



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

            if selected_type == "counter_data":
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
                        date = row[0]  # assuming the date is in the second column
                        record = {
                            "(Ing) Ingressi": row[1] or 0,
                            "(Est) Traffico Esterno": row[2] or 0,
                            "(TA) Tasso di Attrazione": row[3] or 0,
                        }

                        # mar-19.11.24 to YYYY/MM/DD
                        date = date.split("-")[1]
                        date = datetime.strptime(date, "%d.%m.%y").strftime("%Y-%m-%d")


                        # If the date is already a key, overwrite the current record
                        if date in data_dict:

                            data_dict[date] = record
                        else:
                            # Otherwise, create a new list with the record
                            data_dict[date] = [record]


                        data_dict[date] = [record]


                    for date, records in data_dict.items():
                        if Import.objects.filter(branch=branch_obj, import_date=date, import_type=selected_type).exists():
                            errors.append(f"Collision on {date}")
                            continue


                    if errors:
                        return JsonResponse({"status": "error", "errors": errors}, status=200)

                    import_bulk_create_list = []
                    for date, data in data_dict.items():
                        i = Import(import_date=date, data=data, branch=branch_obj, import_type=selected_type)
                        import_bulk_create_list.append(i)

                    Import.objects.bulk_create(import_bulk_create_list)

                    return JsonResponse({"status": "success"}, status=200)

            ### START CONVERTING DATA
            elif selected_type == "sales_data":
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
                        i = Import(import_date=date_str, data=data, branch=branch_obj, import_type=selected_type)
                        import_bulk_create_list.append(i)

                    Import.objects.bulk_create(import_bulk_create_list)


                return JsonResponse({"status" : "success", "errors": []}, status=200)

        elif branch_obj.get_brand() == "original":
            print("original")

            if selected_type == "counter_data":
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



                        date = row[0]  # assuming the date is in the second column
                        record = {
                            "(Ing) Ingressi": row[1],
                            "(Est) Traffico Esterno": row[2],
                            "(TA) Tasso di Attrazione": row[3],
                        }

                        data_dict[date] = [record]

                    print(data_dict)


            ### START CONVERTING DATA
            elif selected_type == "sales_data":

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
                        i = Import(import_date=date, data=data, branch=branch_obj, import_type=selected_type)
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

        elif filter_type == "counter":

            redirect_url = "/report_counter?branch={}&date={}".format(branch, date)

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

        return render(request, "frontend/report/branch.html", context)

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
from .forms import EmployeeForm, ScheduleForm


def new_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('all_employees')  # Change this to whatever view or URL you want
    else:
        form = EmployeeForm()

    return render(request, 'frontend/employees/new.html', {'form': form})


def report_counter(request):
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
        ingressi = f.generate_ingressi_branch_report(branch_id, date_start, date_end)
        ingressi_total = int(sum(ingressi.values()))  ## TOTALE SCONTRINI

        branch = Branch.objects.get(id=branch_id)

        attrazione = f.generate_branch_tasso_attrazione_report(branch_id, date_start, date_end)
        attrazione_total = sum(attrazione.values())  / len(attrazione)
        attrazione_total = round(attrazione_total, 2)

        traffico_esterno = f.generate_branch_traffico_esterno_report(branch_id, date_start, date_end)
        traffico_esterno_total = sum(traffico_esterno.values())

        pprint(ingressi)

        zoom_enabled = "false"
        graph_type = "area"

        if len(attrazione) > 30:
            zoom_enabled = "true"
            graph_type = "area"

        context = {
            "branch": branch,
            "brand": branch.get_brand(),

            "date_start": date_start,
            "date_end": date_end,

            "ingressi": ingressi,
            "ingressi_total": ingressi_total,
            "attrazione": attrazione,
            "attrazione_total": attrazione_total,
            "traffico_esterno": traffico_esterno,
            "traffico_esterno_total": traffico_esterno_total,

            "zoom_enabled": zoom_enabled,
            "type": graph_type,
        }

        return render(request, "frontend/report/counter.html", context=context)

    # Optionally handle non-GET requests
    return JsonResponse({"status": "error", "errors": ["Invalid request method"]}, status=405)


from django_tables2 import SingleTableView
from django_filters.views import FilterView
from .tables import SchedulesTable
from .filters import ScheduleFilter  # Make sure ScheduleFilter is imported


class ScheduleListView(FilterView, SingleTableView):
    model = Schedule
    table_class = SchedulesTable
    template_name = "frontend/schedules/all.html"
    filterset_class = ScheduleFilter  # This should be your filterset class

    # You do not need to override `get_queryset` because `FilterView` handles it
    # If you still need custom logic, you can override `get_filterset` or `get_queryset` accordingly.

    # If overriding `get_queryset`, make sure it's using the filter:
    def get_queryset(self):
        # Default filtering is handled by the FilterView, but you can still customize here if needed.
        return Schedule.objects.all()  # Return all schedules if no filters applied


def new_schedule(request):
    if request.method == 'POST':
        form = ScheduleForm(request.POST)

        if form.is_valid():
            # Save the Orario instance
            new_sch = form.save()
            request.session['new_schedule_pk'] = new_sch.pk
            return redirect("config_schedule") #### redirect here with parameter
        else:
            print(form.errors)


    else:
        form = ScheduleForm()

    # If you want to render the employees separately in the template,
    # you can pass them in context.
    # Build a mapping of branch id -> list of employees (id, name, surname)
    employees_by_branch = {}
    for branch in Branch.objects.all():
        emps = Employee.objects.filter(branch=branch)
        employees_by_branch[branch.id] = list(emps.values("id", "first_name", "last_name"))

    context = {
        'form': form,
        # Pass the mapping as JSON so we can use it in JS.
        'employees_by_branch': json.dumps(employees_by_branch),
    }
    return render(request, "frontend/schedules/new.html", context=context)


def config_schedule(request):
    if request.method == "GET":
        new_schedule_pk = request.session.get('new_schedule_pk')
        schedule = Schedule.objects.get(pk=new_schedule_pk)
        employees = []
        for employee in schedule.employees:
            employees.append(Employee.objects.get(id=employee))

        # Serialize the shift data if it exists, otherwise use an empty list.
        prefilled_shifts = json.dumps(schedule.shift_data) if schedule.shift_data else '[]'

        free_days_map = {}
        if schedule.free_days:
            for entry in schedule.free_days:
                # Use the employee_id as string for easier lookup from HTML (data attributes are strings)
                free_days_map[str(entry.get("employee_id"))] = entry.get("free_days", [])
        # Convert to JSON so we can use it in JavaScript
        free_days_json = json.dumps(free_days_map)

        context = {
            "schedule": schedule,
            "employees": employees,
            "prefilled_shifts": prefilled_shifts,  # Pass the JSON string to the template.
            "free_days": free_days_json,  # JSON string mapping employee_id to free days

        }
        return render(request, "frontend/schedules/config.html", context=context)

    elif request.method == "POST":
        form_data = request.POST
        print(form_data)
        # Get and parse shifts data from request
        shifts_data = request.POST.get('shifts_data', '[]')  # Default to empty list if no shifts
        shifts = json.loads(shifts_data)

        new_schedule_pk = request.session.get('new_schedule_pk')
        schedule = Schedule.objects.get(pk=new_schedule_pk)

        # Convert minutes to HH:MM format
        if shifts != schedule.shift_data:
            for shift in shifts:
                shift["start"] = str(timedelta(minutes=shift["start"]))[:-3]  # Converts to HH:MM
                shift["end"] = str(timedelta(minutes=shift["end"]))[:-3]
            schedule.shift_data = shifts

        schedule.free_days = process_free_days(form_data)

        schedule.save()

        return redirect("confirm_schedule")


import json


def process_free_days(form_data):
    """
    Extract free days from the POST data.
    Returns a list of dictionaries, e.g.:
    [
        {"employee_id": 1, "free_days": ["2025-02-01", "2025-02-07", "2025-02-14"]},
        {"employee_id": 2, "free_days": ["2025-02-12", "2025-02-19", "2025-02-26"]},
        # ...
    ]
    """
    free_days_data = []

    # Loop through all keys in form_data.
    for key in form_data:
        if key.startswith("free_days_"):
            # Extract the employee ID from the key.
            employee_id_str = key.split("_")[-1]
            try:
                employee_id = int(employee_id_str)
            except ValueError:
                # Skip if employee_id isn't an integer.
                continue

            # Get the value (a list with one string element).
            free_days_value = form_data.get(key, "").strip()

            # Split the dates by comma and remove extra spaces.
            if free_days_value:
                days_list = [day.strip() for day in free_days_value.split(",") if day.strip()]
            else:
                days_list = []

            free_days_data.append({
                "employee_id": employee_id,
                "free_days": days_list,
            })

    return free_days_data


def confirm_schedule(request):
    if request.method == "GET":
        new_schedule_pk = request.session.get('new_schedule_pk')
        schedule = Schedule.objects.get(pk=new_schedule_pk)

        # Build a mapping for free days:
        free_days_map = {}
        if schedule.free_days:
            for entry in schedule.free_days:
                free_days_map[str(entry.get("employee_id"))] = entry.get("free_days", [])

        # Build a list of employee objects and annotate with free_days:
        employees = []
        for employee_id in schedule.employees:
            try:
                emp = Employee.objects.get(id=employee_id)
                # Annotate the employee object with its free days:
                emp.free_days = free_days_map.get(str(emp.id), [])
                employees.append(emp)
            except Employee.DoesNotExist:
                pass

        context = {
            "schedule": schedule,
            "employees": employees,
            # You can still pass free_days mapping if needed for other purposes:
            "free_days": free_days_map,
        }
        return render(request, "frontend/schedules/confirm.html", context=context)


def create_schedule(request):
    if request.method == "POST":
        new_schedule_pk = request.session.get('new_schedule_pk')
        schedule = Schedule.objects.get(pk=new_schedule_pk)
        from frontend.orario_creation import create_scheduleMP

        create_scheduleMP(schedule.id)

def timeline_schedule(request):
    if request.method == "GET":
        new_schedule_pk = request.session.get('new_schedule_pk')
        schedule = Schedule.objects.get(pk=new_schedule_pk)
        context = {
            "schedule": schedule,
        }
        return render(request, "frontend/schedules/timeline.html", context=context)


