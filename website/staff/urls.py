from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('specs/', views.spec_search, name='spec_search'),
    path('spec/<int:id>/edit/', views.spec_edit, name='spec_edit'),
    path('rental/<int:id>/', views.rental_detail, name='rental_detail'),
    path('rental/<int:id>/edit/', views.rental_edit, name='rental_edit'),
    path('rental/<int:id>/quickedit/', views.rental_quickedit, name='rental_quickedit'),
    path('rental/<int:id>/qr/', views.rental_qr, name='rental_qr'),
    path('rental/<int:machine_id>/newhire/', views.new_hire, name='new_hire'),
    path('spec/<int:id>/', views.spec_detail, name='spec_detail'),
    path('rental/add/', views.rental_add, name='rental_add'),
    path('rental/<int:id>/delete/', views.rental_delete, name='rental_delete'),
    path('customers/add/', views.customer_add, name='customer_add'),
    path('jobs/', views.service_jobs, name='service_jobs'),                    # ✅ list
    path('jobs/<int:id>/', views.service_job_detail, name='service_job_detail'),  # ✅ detail
    path('jobs/<int:id>/qr/', views.service_job_qr, name='service_job_qr'),       # ✅ QR (links to detail)
    path('jobs/new/', views.service_job_create, name='service_job_create'),
    path('inventory/', views.inventory, name='inventory'),
    path('inventory/part/<int:id>/qr/', views.part_qr, name='part_qr'),
    path('inventory/part/<int:id>/take/', views.part_take, name='part_take'),
]
