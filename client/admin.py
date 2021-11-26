from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import ugettext_lazy as _

from .models import *

@admin.register(User)
class UserAdmin(DjangoUserAdmin):

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email',),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username', 'email',)

@admin.register(Vacation)
class VacationAdmin(admin.ModelAdmin):
    list_display = ('id',
    'user',
    'vacation_start',
    'vacation_end',)

    list_filter = ('user', 'vacation_start', 'vacation_end',)
    search_fields = ('user', 'vacation_start', 'vacation_end',)

@admin.register(HolidayVacation)
class HolidayVacationAdmin(admin.ModelAdmin):
    list_display = ('id',
    'user',
    'vacation',
    'get_vacation_date',
    'count_holiday',
    'vac_start',
    'new_vacation_end',)

@admin.register(OutOffice)
class OutOfficeAdmin(admin.ModelAdmin):
    list_display = ('id',
    'user',
    'out_office_start',
    'out_office_end',)

    list_filter = ('user', 'out_office_start', 'out_office_end',)
    search_fields = ('user', 'out_office_start', 'out_office_end',)

@admin.register(DayOff)
class DayOffAdmin(admin.ModelAdmin):
    list_display = ('id',
    'user',
    'day_off_start',
    'day_off_end',)

    list_filter = ('user', 'day_off_start', 'day_off_end',)
    search_fields = ('user', 'day_off_start', 'day_off_end',)

@admin.register(Sick)
class SickAdmin(admin.ModelAdmin):
    list_display = ('id',
    'user',
    'sick_start',
    'sick_end',)

    list_filter = ('user', 'sick_start', 'sick_end',)
    search_fields = ('user', 'sick_start', 'sick_end',)
