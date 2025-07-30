from django import forms
from .models import MachineSpecification, Expense, Customer, RentalRecord

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
        fields = ['first_name', 'last_name', 'phone', 'email', 'address', 'notes']

class RentalRecordForm(forms.ModelForm):
    class Meta:
        model = RentalRecord
        fields = ['start_date', 'due_date', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }