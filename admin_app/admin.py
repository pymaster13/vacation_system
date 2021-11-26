from django.contrib import admin
from .models import *

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'holiday_start', 'holiday_end',)
    list_filter = ('name', 'holiday_start', 'holiday_end',)
    search_fields = ('name', 'holiday_start', 'holiday_end',)
