from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Count
from .models import RentalMachine, MachineSpecification, RentalRecord, Job, StaffProfile, ActivityLog, Timesheet, Expense, Customer
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .forms import MachineSpecificationForm, ExpenseForm


@login_required
def dashboard(request):
    q = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    tier_filter = request.GET.get('tier', '')

    machines = RentalMachine.objects.all()

    # Search
    if q:
        machines = machines.filter(
            brand__icontains=q
        ) | machines.filter(
            model__icontains=q
        ) | machines.filter(
            serial_number__icontains=q
        )

    # Filters
    if status_filter:
        machines = machines.filter(status=status_filter)
    if tier_filter:
        machines = machines.filter(value_tier=tier_filter)

    # Count totals by status
    counts = RentalMachine.objects.values('status').annotate(total=Count('id'))
    status_summary = {item['status']: item['total'] for item in counts}
    print("DEBUG COUNTS:", status_summary)
    return render(request, 'staff/dashboard.html', {
        'machines': machines,
        'q': q,
        'status_filter': status_filter,
        'tier_filter': tier_filter,
        'status_summary': status_summary,
    })


@login_required
def rental_detail(request, id):
    machine = get_object_or_404(RentalMachine, id=id)
    service_history = Job.objects.filter(treadmill__serial_number=machine.serial_number).order_by('-date_created')
    rental_history = RentalRecord.objects.filter(machine=machine).order_by('-start_date')
    return render(request, 'staff/rental_detail.html', {
        'machine': machine,
        'service_history': service_history,
        'rental_history': rental_history
    })


@login_required
@csrf_exempt
def rental_quickedit(request, id):
    if request.method == 'POST':
        machine = get_object_or_404(RentalMachine, id=id)
        import json
        data = json.loads(request.body)
        field = data.get('field')
        value = data.get('value')

        VALID_STATUSES = ["available", "rented", "maintenance", "retired"]
        VALID_TIERS = ["low", "medium", "high", "commercial"]

        if field == "status" and value not in VALID_STATUSES:
            return JsonResponse({"success": False, "error": "Invalid status"})

        if field == "value_tier" and value not in VALID_TIERS:
            return JsonResponse({"success": False, "error": "Invalid value tier"})

        if hasattr(machine, field):
            setattr(machine, field, value)
            machine.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "error": "Invalid field"})
    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def rental_edit(request, id):
    machine = get_object_or_404(RentalMachine, id=id)
    if request.method == 'POST':
        machine.status = request.POST.get('status')
        machine.location = request.POST.get('location')
        machine.notes = request.POST.get('notes')
        machine.condition = request.POST.get('condition')
        machine.value_tier = request.POST.get('value_tier')
        machine.save()
        return render(request, 'staff/rental_detail.html', {'machine': machine})
    return render(request, 'staff/rental_edit.html', {'machine': machine})


@login_required
def rental_qr(request, id):
    import qrcode
    from io import BytesIO
    from django.http import HttpResponse
    machine = get_object_or_404(RentalMachine, id=id)
    url = request.build_absolute_uri(f"/staff/rental/{machine.id}/")
    qr = qrcode.make(url)
    buffer = BytesIO()
    qr.save(buffer)
    buffer.seek(0)
    return HttpResponse(buffer.read(), content_type="image/png")


def spec_search(request):
    query = request.GET.get('q', '')
    specs = MachineSpecification.objects.all()
    if query:
        specs = specs.filter(model__icontains=query) | specs.filter(brand__icontains=query)
    return render(request, 'staff/spec_search.html', {'specs': specs, 'q': query})


def spec_edit(request, id):
    spec = get_object_or_404(MachineSpecification, id=id)

    if request.method == "POST":
        form = MachineSpecificationForm(request.POST, request.FILES, instance=spec)
        if form.is_valid():
            form.save()
            return redirect('staff:spec_detail', id=spec.id)
    else:
        form = MachineSpecificationForm(instance=spec)

    return render(request, 'staff/spec_edit.html', {'form': form, 'spec': spec})


@login_required
def spec_detail(request, id):
    spec = get_object_or_404(MachineSpecification, id=id)
    return render(request, 'staff/spec_detail.html', {'spec': spec})


@login_required
def profile_view(request):
    profile = get_object_or_404(StaffProfile, user=request.user)
    recent_activities = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')[:10]
    timesheets = Timesheet.objects.filter(user=request.user).order_by('-date')
    expenses = Expense.objects.filter(user=request.user).order_by('-date')

    if request.method == 'POST':
        expense_form = ExpenseForm(request.POST)
        if expense_form.is_valid():
            new_expense = expense_form.save(commit=False)
            new_expense.user = request.user
            new_expense.save()
            return redirect('staff:profile')
    else:
        expense_form = ExpenseForm()

    return render(request, 'staff/profile.html', {
        'profile': profile,
        'recent_activities': recent_activities,
        'timesheets': timesheets,
        'expenses': expenses,
        'expense_form': expense_form,
    })


def new_hire(request, machine_id):
    machine = get_object_or_404(RentalMachine, id=machine_id)
    customers = Customer.objects.all()

    if request.method == "POST":
        if request.POST.get("add_customer"):
            # --- Adding a new customer ---
            first_name = request.POST.get("first_name")
            phone = request.POST.get("phone")
            email = request.POST.get("email")
            address = request.POST.get("address")
            customer = Customer.objects.create(
                first_name=first_name,
                phone=phone,
                email=email,
                address=address
            )
        else:
            # --- Selecting an existing customer ---
            customer_id = request.POST.get("customer")
            customer = get_object_or_404(Customer, id=customer_id)

        # Create rental record
        start_date = request.POST.get("start_date")
        due_date = request.POST.get("due_date")
        notes = request.POST.get("notes")

        rental = RentalRecord.objects.create(
            machine=machine,
            customer=customer,
            start_date=start_date,
            due_date=due_date,
            notes=notes
        )

        # Update machine status
        machine.status = "rented"
        machine.save()

        return redirect('staff:rental_detail', machine.id)

    return render(request, 'staff/new_hire.html', {
        'machine': machine,
        'customers': customers
    })
