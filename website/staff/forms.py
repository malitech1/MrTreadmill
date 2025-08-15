from django import forms
from .models import MachineSpecification, Expense, Customer, RentalRecord, Job, RentalMachine

class MachineSpecificationForm(forms.ModelForm):
    class Meta:
        model = MachineSpecification
        fields = [
            'brand', 'model', 'motor_model', 'lcb_model', 'running_belt_size',
            'bolt_types', 'incline_motor', 'speed_sensor', 'lubricant_type',
            'voltage_rating', 'current_rating', 'notes', 'image', 'manual_file'
        ]


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['description', 'amount']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'phone', 'email', 'street_address', 'suburb', 'postcode', 'notes']

class RentalRecordForm(forms.ModelForm):
    class Meta:
        model = RentalRecord
        fields = ['start_date', 'due_date', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }


class ServiceJobForm(forms.ModelForm):
    MACHINE_OWNER_CHOICES = (
        ('company', 'Company machine (from rental fleet)'),
        ('customer', 'Customer machine'),
    )

    owner = forms.ChoiceField(
        choices=MACHINE_OWNER_CHOICES,
        widget=forms.RadioSelect,
        initial='company',
        help_text="Is this job for a company (fleet) machine or a customer’s machine?"
    )

    # If owner=company
    rental_machine = forms.ModelChoiceField(
        queryset=RentalMachine.objects.all().order_by('brand', 'model', 'serial_number'),
        required=False,
        help_text="Pick a machine from your rental fleet."
    )

    # If owner=customer
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all().order_by('first_name', 'last_name'),
        required=False,
        help_text="Pick the customer this job is for."
    )
    external_brand = forms.CharField(required=False, max_length=100)
    external_model = forms.CharField(required=False, max_length=100)
    external_serial = forms.CharField(required=False, max_length=100)

    booking_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    confirmed = forms.BooleanField(required=False)

    status = forms.ChoiceField(
        choices=Job.STATUS_CHOICES,
        initial='to_assess'
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3})
    )

    class Meta:
        model = Job
        fields = [
            'owner',
            'rental_machine',
            'customer', 'external_brand', 'external_model', 'external_serial',
            'booking_date', 'confirmed', 'status', 'notes'
        ]

    def clean(self):
        cleaned = super().clean()
        owner = cleaned.get('owner')

        if owner == 'company':
            if not cleaned.get('rental_machine'):
                self.add_error('rental_machine', "Please select a rental machine.")
            # clear customer/external fields
            cleaned['customer'] = None
            cleaned['external_brand'] = ''
            cleaned['external_model'] = ''
            cleaned['external_serial'] = ''
        elif owner == 'customer':
            if not cleaned.get('customer'):
                self.add_error('customer', "Please select a customer.")
            # external fields are optional but useful – no hard requirement
            cleaned['rental_machine'] = None
        else:
            self.add_error('owner', "Please choose who owns this machine.")

        return cleaned

