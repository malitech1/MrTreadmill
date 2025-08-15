from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Count
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from .models import (
    RentalMachine, MachineSpecification, RentalRecord, Job,
    StaffProfile, ActivityLog, Timesheet, Expense, Customer,
    Part, PartUsage
)
from .forms import MachineSpecificationForm, ExpenseForm, CustomerForm, ServiceJobForm
from qrcode.image.svg import SvgImage  # ✅ SVG output avoids Pillow/zlib issues
import qrcode
from io import BytesIO


def admin_required(view_func):
    return user_passes_test(lambda u: u.is_staff)(view_func)


@login_required
def dashboard(request):
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    tier_filter = request.GET.get('tier', '')

    machines = RentalMachine.objects.all()

    # Search (Q to preserve chaining)
    if q:
        machines = machines.filter(
            Q(brand__icontains=q) |
            Q(model__icontains=q) |
            Q(serial_number__icontains=q)
        )

    # Filters
    if status_filter:
        machines = machines.filter(status=status_filter)
    if tier_filter:
        machines = machines.filter(value_tier=tier_filter)

    # Totals
    total_machines = RentalMachine.objects.count()
    counts = RentalMachine.objects.values('status').annotate(total=Count('id'))
    status_summary = {row['status']: row['total'] for row in counts}

    return render(request, 'staff/dashboard.html', {
        'machines': machines,                # ✅ pass queryset, not wrapped objects
        'q': q,
        'status_filter': status_filter,
        'tier_filter': tier_filter,
        'status_summary': status_summary,
        'total_machines': total_machines,    # ✅ template expects this
    })


@login_required
def rental_detail(request, id):
    machine = get_object_or_404(RentalMachine, id=id)
    service_history = Job.objects.filter(
        treadmill__serial_number=machine.serial_number
    ).order_by('-date_created')
    rental_history = RentalRecord.objects.filter(
        machine=machine
    ).select_related('customer').order_by('-start_date')
    return render(request, 'staff/rental_detail.html', {
        'machine': machine,
        'service_history': service_history,
        'rental_history': rental_history
    })


@login_required
@admin_required
def rental_add(request):
    if request.method == 'POST':
        brand = request.POST.get('brand', '').strip()
        model = request.POST.get('model', '').strip()
        serial = request.POST.get('serial_number', '').strip()
        status = request.POST.get('status', 'available')

        if not (brand and model and serial):
            messages.error(request, "Brand, model and serial are required.")
            return render(request, 'staff/rental_add.html')

        RentalMachine.objects.create(
            type='treadmill',  # ✅ default to something valid
            brand=brand,
            model=model,
            serial_number=serial,
            status=status
        )
        messages.success(request, "Rental machine added.")
        return redirect('staff:dashboard')
    return render(request, 'staff/rental_add.html')


@login_required
@admin_required
def rental_delete(request, id):
    machine = get_object_or_404(RentalMachine, id=id)
    machine.delete()
    messages.success(request, "Machine deleted.")
    return redirect('staff:dashboard')


@login_required
def rental_quickedit(request, id):
    # ✅ Keep CSRF protection; your fetch already sends the token header.
    if request.method == 'POST':
        machine = get_object_or_404(RentalMachine, id=id)
        import json
        data = json.loads(request.body or "{}")
        field = data.get('field')
        value = data.get('value')

        VALID_STATUSES = {"available", "rented", "maintenance", "retired"}
        VALID_TIERS = {"low", "medium", "high", "commercial"}

        if field == "status" and value not in VALID_STATUSES:
            return JsonResponse({"success": False, "error": "Invalid status"})
        if field == "value_tier" and value not in VALID_TIERS:
            return JsonResponse({"success": False, "error": "Invalid value tier"})

        if hasattr(machine, field):
            setattr(machine, field, value)
            machine.save(update_fields=[field])
            return JsonResponse({"success": True})
        return JsonResponse({"success": False, "error": "Invalid field"})
    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def rental_edit(request, id):
    machine = get_object_or_404(RentalMachine, id=id)
    if request.method == 'POST':
        machine.status = request.POST.get('status') or machine.status
        machine.location = request.POST.get('location', '')
        machine.notes = request.POST.get('notes', '')
        machine.condition = request.POST.get('condition') or machine.condition
        machine.value_tier = request.POST.get('value_tier') or machine.value_tier
        machine.save()
        messages.success(request, "Machine details updated successfully.")
        return redirect('staff:rental_detail', id=machine.id)
    return render(request, 'staff/rental_edit.html', {'machine': machine})


@login_required
def rental_qr(request, id):
    """Return a small SVG QR that links to the machine’s detail page.
       ✅ Uses SVG to avoid Pillow/zlib dependency entirely."""
    machine = get_object_or_404(RentalMachine, id=id)
    url = request.build_absolute_uri(f"/staff/rental/{machine.id}/")

    qr = qrcode.QRCode(
        version=1, box_size=2, border=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(image_factory=SvgImage)  # SVG output
    buffer = BytesIO()
    img.save(buffer)
    svg_data = buffer.getvalue()
    return HttpResponse(svg_data, content_type="image/svg+xml")


def spec_search(request):
    query = request.GET.get('q', '').strip()
    specs = MachineSpecification.objects.all()
    if query:
        specs = specs.filter(Q(model__icontains=query) | Q(brand__icontains=query))
    return render(request, 'staff/spec_search.html', {'specs': specs, 'q': query})


def spec_edit(request, id):
    spec = get_object_or_404(MachineSpecification, id=id)
    if request.method == "POST":
        form = MachineSpecificationForm(request.POST, request.FILES, instance=spec)
        if form.is_valid():
            form.save()
            messages.success(request, "Specification saved.")
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
            messages.success(request, "Expense added.")
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


@login_required
def new_hire(request, machine_id):
    machine = get_object_or_404(RentalMachine, id=machine_id)
    customers = Customer.objects.all().order_by('first_name', 'last_name')

    if request.method == "POST":
        # Are we adding a brand new customer?
        is_new = bool(request.POST.get("add_customer"))

        if is_new:
            first_name = (request.POST.get("first_name") or "").strip()
            last_name  = (request.POST.get("last_name") or "").strip()
            phone      = (request.POST.get("phone") or "").strip()
            email      = (request.POST.get("email") or "").strip()
            street_address = (request.POST.get("street_address") or "").strip()
            suburb     = (request.POST.get("suburb") or "").strip()
            postcode = (request.POST.get("postcode") or "").strip()

            if not first_name or not last_name:
                messages.error(request, "First and last name are required for a new customer.")
                # ✅ ALWAYS return a response, even after errors
                return render(request, "staff/new_hire.html", {
                    "machine": machine,
                    "customers": customers,
                })

            customer = Customer.objects.create(
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                email=email,
                street_address=street_address,
                suburb=suburb,
                postcode=postcode,
            )
        else:
            customer_id = request.POST.get("customer")
            if not customer_id:
                messages.error(request, "Please select an existing customer or add a new one.")
                return render(request, "staff/new_hire.html", {
                    "machine": machine,
                    "customers": customers,
                })
            customer = get_object_or_404(Customer, id=customer_id)

        # Rental fields
        start_date = request.POST.get("start_date")
        due_date   = request.POST.get("due_date")
        notes      = request.POST.get("notes", "")

        if not start_date or not due_date:
            messages.error(request, "Start and due dates are required.")
            return render(request, "staff/new_hire.html", {
                "machine": machine,
                "customers": customers,
            })

        RentalRecord.objects.create(
            machine=machine,
            customer=customer,
            start_date=start_date,
            due_date=due_date,
            notes=notes,
        )

        # Update machine status & location to customer suburb/address
        machine.status   = "rented"
        machine.location = (customer.suburb or customer.street_address or "").strip() or "On Hire"
        machine.save(update_fields=["status", "location"])

        messages.success(request, "Hire started.")
        return redirect("staff:rental_detail", id=machine.id)

    # ✅ GET request: always return the form
    return render(request, "staff/new_hire.html", {
        "machine": machine,
        "customers": customers,
    })


@login_required
def customer_add(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer added.")
            return redirect('staff:dashboard')
    else:
        form = CustomerForm()
    return render(request, 'staff/customer_add.html', {'form': form})


@login_required
def service_jobs(request):
    """List all service jobs with key info."""
    jobs = (Job.objects
                .select_related('rental_machine', 'treadmill', 'customer')
                .order_by('-booking_date', '-date_created'))

    return render(request, 'staff/service_jobs.html', {
        'jobs': jobs
    })


@login_required
def service_job_detail(request, id):
    job = get_object_or_404(Job, id=id)
    return render(request, 'staff/service_job_detail.html', {'job': job})


@login_required
def service_job_qr(request, id):
    """Small SVG QR linking to the service job detail."""
    job = get_object_or_404(Job, id=id)
    url = request.build_absolute_uri(f"/staff/jobs/{job.id}/")
    qr = qrcode.QRCode(version=1, box_size=2, border=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(image_factory=SvgImage)
    buffer = BytesIO()
    img.save(buffer)
    return HttpResponse(buffer.getvalue(), content_type="image/svg+xml")

login_required
def service_job_create(request):
    if request.method == 'POST':
        form = ServiceJobForm(request.POST)
        if form.is_valid():
            job: Job = form.save(commit=False)

            # If company machine, mirror identifiers from rental machine into the legacy Treadmill field if you like
            # (Optional: only if you still use Job.treadmill elsewhere)
            # For display we rely on rental_machine/customer + external_* in the list/detail templates.

            job.save()
            messages.success(request, f"Service job #{job.id} created.")
            return redirect('staff:service_job_detail', id=job.id)
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = ServiceJobForm()

    return render(request, 'staff/service_job_create.html', {'form': form})


@login_required
def inventory(request):
    """Inventory overview: all rental machines + all parts with QR links."""
    q = (request.GET.get('q') or '').strip()

    machines = RentalMachine.objects.all().order_by('brand', 'model', 'serial_number')
    parts = Part.objects.all().order_by('name', 'part_number')

    if q:
        machines = machines.filter(
            Q(brand__icontains=q) | Q(model__icontains=q) | Q(serial_number__icontains=q)
        )
        parts = parts.filter(
            Q(name__icontains=q) | Q(part_number__icontains=q) | Q(compatible_models__icontains=q)
        )

    return render(request, 'staff/inventory.html', {
        'machines': machines,
        'parts': parts,
        'q': q,
    })


@login_required
def part_qr(request, id):
    """One QR per Part type: opens the take page for that part."""
    part = get_object_or_404(Part, id=id)
    url = request.build_absolute_uri(f"/staff/inventory/part/{part.id}/take/")
    qr = qrcode.QRCode(version=1, box_size=2, border=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(image_factory=SvgImage)
    buf = BytesIO()
    img.save(buf)
    return HttpResponse(buf.getvalue(), content_type="image/svg+xml")

@user_passes_test(lambda u: u.is_staff)
@login_required
def part_take(request, id):
    """
    Scan the part QR → confirm/remove stock.
    Creates a PartUsage row (no job/rental link), and our PartUsage.save() will adjust stock.
    """
    part = get_object_or_404(Part, id=id)

    if request.method == 'POST':
        try:
            qty = int(request.POST.get('quantity', '1'))
        except ValueError:
            qty = 0

        if qty <= 0:
            messages.error(request, "Quantity must be a positive number.")
            return redirect('staff:part_take', id=part.id)

        if part.quantity_in_stock <= 0:
            messages.error(request, f"No stock available for {part.name}.")
            return redirect('staff:part_take', id=part.id)

        # Clamp to available stock (so we never go negative)
        if qty > part.quantity_in_stock:
            qty = part.quantity_in_stock
            messages.info(request, f"Only {qty} in stock, using that amount.")

        # Create usage record (no job/rental_record); PartUsage.save() will decrement stock.
        PartUsage.objects.create(part=part, quantity_used=qty)

        messages.success(request, f"Removed {qty} from stock for {part.name}.")
        return redirect('staff:inventory')

    # GET → show confirm form
    return render(request, 'staff/part_take.html', {'part': part})