from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'status', 'site')
    list_filter = ('status', 'date', 'site')
    search_fields = ('employee__name',)
    date_hierarchy = 'date'
