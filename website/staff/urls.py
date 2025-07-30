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
]
