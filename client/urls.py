from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import * 

urlpatterns = [
    path('add_vacation/', add_vacation , name='add_vacation'),
    path('add_sick/', add_sick , name='add_sick'),
    path('add_day_off/', add_day_off , name='add_day_off'),
    path('add_out_office/', add_out_office , name='add_out_office'),

    path('choice_login/', choice_login , name='choice_login'),
    path('login/', user_login , name='login'),
    path('login_email/', user_login_email , name='login_email'),
    path('logout/', user_logout , name='logout'),

    path('user_panel/', user_panel , name='user_panel'),
    path('user_panel_error/', user_panel_error , name='user_panel_error'),

    path('vacations_list/', vacations_list , name='vacations_list'),

    path('delete_sick/', delete_sick , name='delete_sick'),
    path('delete_day_off/', delete_day_off , name='delete_day_off'),
    path('delete_out_office/', delete_out_office , name='delete_out_office'),

    path('', index, name='index'),

]  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
