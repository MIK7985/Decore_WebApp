from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('employees/', include('employees.urls')),
    path('sites/', include('sites_mgmt.urls')),
    path('attendance/', include('attendance.urls')),
    path('salary/', include('salary.urls')),
    path('payments/', include('payments.urls')),
    path('reports/', include('reports.urls')),
    path('inventory/', include('inventory.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Decore Developers Admin"
admin.site.site_title = "Decore Developers"
admin.site.index_title = "POP Work Management"
