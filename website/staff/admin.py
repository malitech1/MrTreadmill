from django.contrib import admin
from .models import (
    RentalMachine,
    MachineSpecification,
    RentalRecord,
    Job,
    Part,
    PartUsage,
    StaffProfile,
    ActivityLog,
    Timesheet,
    Expense
)

@admin.register(RentalMachine)
class RentalMachineAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'brand', 'model', 'status', 'location', 'value_tier')
    search_fields = ('serial_number', 'brand', 'model')
    list_filter = ('status', 'value_tier', 'condition')

@admin.register(MachineSpecification)
class MachineSpecificationAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'motor_model', 'lcb_model')
    search_fields = ('brand', 'model', 'motor_model')

@admin.register(RentalRecord)
class RentalRecordAdmin(admin.ModelAdmin):
    list_display = ('machine', 'customer', 'start_date', 'due_date', 'return_date')
    list_filter = ('start_date', 'due_date', 'return_date')

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('treadmill', 'status', 'date_created')
    list_filter = ('status',)
    search_fields = ('treadmill__serial_number',)

@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ('name', 'part_number', 'quantity_in_stock', 'location')
    search_fields = ('name', 'part_number')

@admin.register(PartUsage)
class PartUsageAdmin(admin.ModelAdmin):
    list_display = ('part', 'quantity_used', 'job', 'date_used')
    list_filter = ('date_used',)

admin.site.register(StaffProfile)
admin.site.register(ActivityLog)
admin.site.register(Timesheet)
admin.site.register(Expense)