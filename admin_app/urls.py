from django.urls import path
from .views import *

urlpatterns = [
    path('add_holiday/', add_holiday , name='add_holiday'),
    path('admin_vacation/', admin_vacation , name='admin_vacation'),
    path('admin_vacation_error/', admin_vacation_error , name='admin_vacation_error'),
    path('holidays/', holidays, name='holidays'),
    path('register/', register, name='register'),
    path('staff_info/', staff_info, name='staff_info'),

    path('', admin_index, name='admin_index'),
]
