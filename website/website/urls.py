from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('staff/', include(('staff.urls', 'staff'), namespace='staff')),  # ✅ namespaced
    path('accounts/', include('django.contrib.auth.urls')),  # 👈 this enables login/logout
]