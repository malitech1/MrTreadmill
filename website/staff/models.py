from django.db import models
from django.contrib.auth.models import User

class Technician(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    def __str__(self):
        return self.name


class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    street_address = models.TextField(blank=True, null=True)
    suburb = models.TextField(blank=True, null=True)
    postcode = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class MachineSpecification(models.Model):
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    bolt_types = models.TextField(blank=True)
    running_belt_size = models.CharField(max_length=100, blank=True)
    motor_model = models.CharField(max_length=100, blank=True)
    lcb_model = models.CharField(max_length=100, blank=True)
    incline_motor = models.CharField(max_length=100, blank=True)
    speed_sensor = models.CharField(max_length=100, blank=True)
    lubricant_type = models.CharField(max_length=100, blank=True)
    voltage_rating = models.CharField(max_length=50, blank=True)
    current_rating = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    manual_file = models.FileField(upload_to='manuals/', blank=True, null=True)
    image = models.ImageField(upload_to='machine_images/', blank=True, null=True)

    class Meta:
        unique_together = ('brand', 'model')

    def __str__(self):
        return f"{self.brand} {self.model}"

class Treadmill(models.Model):
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)
    specification = models.ForeignKey(MachineSpecification, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.brand} {self.model} ({self.serial_number})"

class Job(models.Model):
    STATUS_CHOICES = [
        ('to_assess', 'To be assessed'),
        ('in_progress', 'In progress'),
        ('complete', 'Complete'),
        ('cancelled', 'Cancelled'),
    ]

    treadmill = models.ForeignKey(Treadmill, on_delete=models.CASCADE, null=True, blank=True)
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_completed = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    # ✅ New: support booking, explicit status, association to our rental fleet and/or a customer
    booking_date = models.DateField(null=True, blank=True)
    confirmed = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='to_assess')

    # Optional identifiers for a customer’s own machine
    external_brand = models.CharField(max_length=100, blank=True)
    external_model = models.CharField(max_length=100, blank=True)
    external_serial = models.CharField(max_length=100, blank=True)

    # If it’s a company (rental) machine, link here:
    rental_machine = models.ForeignKey('RentalMachine', on_delete=models.SET_NULL, null=True, blank=True)

    # If it’s a customer’s own machine, capture the customer:
    customer = models.ForeignKey('Customer', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        # Show who/what the job is for at a glance
        who = self.customer or self.rental_machine or self.treadmill
        return f"Job #{self.pk} – {who}"


class RentalMachine(models.Model):
    MACHINE_TYPES = [
        ('treadmill', 'Treadmill'),
        ('elliptical', 'Elliptical'),
        ('bike', 'Exercise Bike'),
    ]
    VALUE_TIERS = [
        ('low', 'Low Tier'),
        ('medium', 'Medium Tier'),
        ('high', 'High Tier'),
        ('commercial', 'Commercial Grade'),
    ]
    type = models.CharField(max_length=20, choices=MACHINE_TYPES)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True)
    condition = models.CharField(max_length=100, default='Good')
    status = models.CharField(max_length=20, choices=[
        ('available', 'Available'),
        ('rented', 'Rented'),
        ('maintenance', 'In Maintenance')
    ])
    location = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    specification = models.ForeignKey(MachineSpecification, on_delete=models.SET_NULL, null=True, blank=True)
    value_tier = models.CharField(max_length=20, choices=VALUE_TIERS, default='low')

    def __str__(self):
        return f"{self.brand} {self.model} ({self.serial_number})"

class RentalRecord(models.Model):
    machine = models.ForeignKey('RentalMachine', on_delete=models.CASCADE, related_name='rental_history')
    customer = models.ForeignKey('staff.Customer', on_delete=models.SET_NULL, null=True, blank=True, related_name='rentals')
    start_date = models.DateField()
    due_date = models.DateField()
    return_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.machine.serial_number} rented by {self.customer}"


class Part(models.Model):
    name = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100, unique=True)
    quantity_in_stock = models.IntegerField()
    location = models.CharField(max_length=100, blank=True)
    compatible_models = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.part_number})"

class PartUsage(models.Model):
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True)
    rental_record = models.ForeignKey(RentalRecord, on_delete=models.CASCADE, null=True, blank=True)
    quantity_used = models.IntegerField()
    date_used = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.part.quantity_in_stock -= self.quantity_used
        self.part.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity_used}x {self.part.name}"


class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username} - {self.position}"


class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action}"


class Timesheet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.hours_worked} hrs)"


class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.description})"

