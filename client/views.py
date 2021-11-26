import datetime
from math import floor

from django.core.mail import send_mail
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from admin_app.models import Holiday
from admin_app.views import *
from .models import Vacation, OutOffice, DayOff, Sick, HolidayVacation
from .forms import UserLoginForm, UserLoginEmailForm
from vacation.settings import EMAIL_HOST_USER

User = get_user_model()

def create_holiday_list():
    holidays = Holiday.objects.all().order_by('holiday_start')
    holiday_list = []
    for holiday in holidays:
        if holiday.holiday_start == holiday.holiday_end:
            holiday_list.append(holiday.holiday_start.strftime("%d.%m"))
        else:
            day = holiday.holiday_start
            holiday_list.append(day.strftime("%d.%m"))
            
            while True:
                day = day + datetime.timedelta(days=1)
                holiday_list.append(day.strftime("%d.%m"))
                if (day == holiday.holiday_end):
                    break
    
    return holiday_list


def check_holiday(date_start, date_end):
    holiday_list = create_holiday_list()
    delta = date_end - date_start
    date_step = datetime.timedelta(1)
    date_list = []
    date_list.append(date_start.strftime("%d.%m"))
    
    for a in range(1,delta.days+1):
        temp = date_start + datetime.timedelta(a)
        date_list.append(temp.strftime("%d.%m"))
    count_days = 0
    
    for date in date_list:
        if date in holiday_list:
            count_days += 1
    
    return count_days

def index(request):
    return render(request, 'index.html', {})

def choice_login(request):
    return render(request, 'choice_login.html', {})

def user_login_email(request):
    if request.method == 'POST':
        login_form = UserLoginEmailForm(request.POST)
        
        if login_form.is_valid():
            email = login_form.cleaned_data['email']
            password = login_form.cleaned_data['password']
            
            try:
                login_user = User.objects.get(email = email)
            except:
                login_form = UserLoginEmailForm()
                return render(request, 'login_fail.html', {'login_form': login_form})
            
            user = authenticate(username = login_user.username , password = password, backend='django.contrib.auth.backends.ModelBackend')
            if user is not None:
                if user.is_active:
                    if user.is_staff:
                        login(request, user)
                        return redirect('admin_index')
            
                    login(request, user)
                    return redirect('user_panel')
            
                else:
                    login_form = UserLoginEmailForm()
                    return render(request, 'login_fail.html', {'login_form': login_form})
            
            else:
                login_form = UserLoginEmailForm()
                return render(request, 'login_fail.html', {'login_form': login_form})
    else:
        login_form = UserLoginEmailForm()
        return render(request, 'login_email.html', {'login_form': login_form})

def user_login(request):
    """
    Login user with form's validation
    """

    if request.method == 'POST':
        login_form = UserLoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']
            user = authenticate(username = username , password = password)

            if user is not None:
                if user.is_active:
                    if user.is_staff:
                        login(request, user)
                        return redirect('admin_index')

                    login(request, user)
                    return redirect('user_panel')

                else:
                    login_form = UserLoginForm()
                    return render(request, 'login_fail.html', {'login_form': login_form})

            else:
                login_form = UserLoginForm()
                return render(request, 'login_fail.html', {'login_form': login_form})

    else:
        login_form = UserLoginForm()
        return render(request, 'login.html', {'login_form': login_form})


def user_logout(request):
    logout(request)
    return redirect('index')

def user_panel(request):
    context = {request.user.username : {}}
    delta = datetime.date.today()-request.user.date_joined.date()
    count_vac_days = str(view_vacations(request.user.id, request.user.date_joined.date(), datetime.date.today()))

    work_days2 = calc_work_days(request.user.id)
    work_days = {"work_days":work_days2}

    vacations = Vacation.objects.filter(user = request.user).order_by('vacation_start')
    out_offs = OutOffice.objects.filter(user = request.user).order_by('out_office_start')
    dayoffs = DayOff.objects.filter(user = request.user).order_by('day_off_start')
    sicks = Sick.objects.filter(user = request.user).order_by('sick_start')
    context.update(work_days)
    context.update({"off_days":dayoffs})
    context.update({"out_days":out_offs})
    context.update({"sick_days":sicks})
    context.update({"count_vac_days":count_vac_days})
    new_vac =  HolidayVacation.objects.filter(user = request.user).order_by('vac_start')
    context.update({"new_vac_days":new_vac})

    work_days = calc_work_days(request.user.id)
    all_holidays = Holiday.objects.all()
    all_holidays_days = 0
    for holiday in all_holidays:
        all_holidays_days += holiday.calc_days()

    half_year = 183
    half_vac_days = 14
    year_days = 365
    potential_vacation_days = 28
    vacation_days = 0
    user_work_days = calc_work_days(request.user.id)
    if user_work_days < half_year :
        vacation_days = 0

    elif work_days >= half_year and  work_days < year_days:

        start_of_vacations_days = request.user.date_joined.date() +  datetime.timedelta(half_year)
        end_of_vacation_days = start_of_vacations_days + datetime.timedelta(year_days+all_holidays_days)

        vacations_delta = end_of_vacation_days - start_of_vacations_days

        #Список всех дней, которые можно взять
        list_of_potential_vacation_days = []

        for vacation_day in range(0,vacations_delta.days+1):
            list_of_potential_vacation_days.append(start_of_vacations_days + datetime.timedelta(vacation_day))

        #Список всех дней, которые можно взять с учётом взятых отпусков в этом году
        copy_list_of_potential_vacation_days = list_of_potential_vacation_days.copy()
        list_of_used_vacation_days = []
        user_vacations = Vacation.objects.filter(user = request.user)

        for vacation in user_vacations:
            delta2 = vacation.vacation_end - vacation.vacation_start
            if delta2.days != 0:
                for b in range(0,delta2.days+1):
                    temp = vacation.vacation_start + datetime.timedelta(b)
                    if temp in list_of_potential_vacation_days:
                        list_of_used_vacation_days.append(temp)
                        try:
                            copy_list_of_potential_vacation_days.remove(temp)
                        except:
                            pass

            else:
                if vacation.vacation_start.date() in list_of_potential_vacation_days:
                    list_of_used_vacation_days.append(temp)
                    try:
                        copy_list_of_potential_vacation_days.remove(temp)
                    except:
                        pass

        #Количество дней, которые пользователь может взять в качестве отпуска за этот год
        vacation_days = half_vac_days - len(list_of_used_vacation_days)

    else:
        count_of_work_years = user_work_days/year_days
        work_years = floor(count_of_work_years)
        days_for_delta = work_years*(year_days+all_holidays_days)

        start_of_vacations_days = request.user.date_joined.date() +  datetime.timedelta(days=days_for_delta)
        days_for_delta2 = year_days+all_holidays_days
        end_of_vacation_days = start_of_vacations_days + datetime.timedelta(days_for_delta2)
        vacations_delta = end_of_vacation_days - start_of_vacations_days

        list_of_potential_vacation_days = []

        for vacation_day in range(0,vacations_delta.days+1):
            list_of_potential_vacation_days.append(start_of_vacations_days + datetime.timedelta(vacation_day))

        copy_list_of_potential_vacation_days = list_of_potential_vacation_days.copy()

        if work_years == 1:
            start_of_vacations_days_for_check = request.user.date_joined.date() + \
                datetime.timedelta(days=days_for_delta) - datetime.timedelta(days=182)
            days_for_delta3 = year_days+all_holidays_days
            end_of_vacation_days = start_of_vacations_days_for_check + \
                datetime.timedelta(days_for_delta3) + datetime.timedelta(days=182)
            vacations_delta2 = end_of_vacation_days - start_of_vacations_days_for_check
            list_of_potential_vacation_days_for_check = []

            for vacation_day in range(0,vacations_delta2.days+1):
                list_of_potential_vacation_days_for_check.append(start_of_vacations_days_for_check +
                    datetime.timedelta(vacation_day))
        else:
            start_of_vacations_days_for_check = request.user.date_joined.date() + datetime.timedelta(days=days_for_delta)
            days_for_delta3 = year_days+all_holidays_days
            end_of_vacation_days = start_of_vacations_days_for_check + \
                datetime.timedelta(days_for_delta3) + datetime.timedelta(days=182)
            vacations_delta2 = end_of_vacation_days - start_of_vacations_days_for_check
            list_of_potential_vacation_days_for_check = []

            for vacation_day in range(0,vacations_delta2.days+1):
                list_of_potential_vacation_days_for_check.append(start_of_vacations_days_for_check +
                    datetime.timedelta(vacation_day))

        list_of_used_vacation_days = []
        user_vacations = Vacation.objects.filter(user = request.user)
        
        for vacation in user_vacations:
            delta2 = vacation.vacation_end - vacation.vacation_start
            if delta2.days != 0:
                for b in range(0,delta2.days+1):
                    temp = vacation.vacation_start + datetime.timedelta(b)
                    if temp in list_of_potential_vacation_days_for_check:
                        list_of_used_vacation_days.append(temp)
                        try:
                            copy_list_of_potential_vacation_days.remove(temp)
                        except:
                            pass
        
            else:
                if vacation.vacation_start.date() in list_of_potential_vacation_days_for_check:
                    list_of_used_vacation_days.append(temp)
                    try:
                        copy_list_of_potential_vacation_days.remove(temp)
                    except:
                        pass

        vacation_days = potential_vacation_days - len(list_of_used_vacation_days)
    
    context.update({"vacation_days":vacation_days})

    return render(request, 'user.html', {'context': context, 'vacation_days':vacation_days})

def user_panel_error(request):
    context = {request.user.username : {}}
    delta = datetime.date.today()-request.user.date_joined.date()
    count_vac_days = str(view_vacations(request.user.id, request.user.date_joined.date(), datetime.date.today()))

    work_days2 = calc_work_days(request.user.id)
    work_days = {"work_days":work_days2}

    vacations = Vacation.objects.filter(user = request.user).order_by('vacation_start')
    out_offs = OutOffice.objects.filter(user = request.user).order_by('out_office_start')
    dayoffs = DayOff.objects.filter(user = request.user).order_by('day_off_start')
    sicks = Sick.objects.filter(user = request.user).order_by('sick_start')

    context.update(work_days)
    context.update({"off_days":dayoffs})
    context.update({"out_days":out_offs})
    context.update({"sick_days":sicks})
    context.update({"count_vac_days":count_vac_days})
    new_vac =  HolidayVacation.objects.filter(user = request.user).order_by('vac_start')
    context.update({"new_vac_days":new_vac})

    work_days = calc_work_days(request.user.id)
    all_holidays = Holiday.objects.all()
    all_holidays_days = 0
    for holiday in all_holidays:
        all_holidays_days += holiday.calc_days()

    half_year = 183
    half_vac_days = 14
    year_days = 365
    potential_vacation_days = 28
    vacation_days = 0
    user_work_days = calc_work_days(request.user.id)

    if user_work_days < half_year :
        vacation_days = 0

    elif work_days >= half_year and  work_days < year_days:

        start_of_vacations_days = request.user.date_joined.date() +  datetime.timedelta(half_year)
        end_of_vacation_days = start_of_vacations_days + datetime.timedelta(year_days+all_holidays_days)

        vacations_delta = end_of_vacation_days - start_of_vacations_days

        #Список всех дней, которые можно взять
        list_of_potential_vacation_days = []

        for vacation_day in range(0,vacations_delta.days+1):
            list_of_potential_vacation_days.append(start_of_vacations_days + datetime.timedelta(vacation_day))

        #Список всех дней, которые можно взять с учётом взятых отпусков в этом году
        copy_list_of_potential_vacation_days = list_of_potential_vacation_days.copy()
        list_of_used_vacation_days = []
        user_vacations = Vacation.objects.filter(user = request.user)
        for vacation in user_vacations:
            delta2 = vacation.vacation_end - vacation.vacation_start
            if delta2.days != 0:
                for b in range(0,delta2.days+1):
                    temp = vacation.vacation_start + datetime.timedelta(b)
                    if temp in list_of_potential_vacation_days:
                        list_of_used_vacation_days.append(temp)
                        copy_list_of_potential_vacation_days.remove(temp)
            else:
                if vacation.vacation_start.date() in list_of_potential_vacation_days:
                    list_of_used_vacation_days.append(temp)
                    copy_list_of_potential_vacation_days.remove(temp)

        #Количество дней, которые пользователь может взять в качестве отпуска за этот год
        vacation_days = half_vac_days - len(list_of_used_vacation_days)

    else:
        count_of_work_years = user_work_days/year_days
        work_years = floor(count_of_work_years)
        days_for_delta = work_years*(year_days+all_holidays_days)

        start_of_vacations_days = request.user.date_joined.date() +  datetime.timedelta(days=days_for_delta)
        days_for_delta2 = year_days+all_holidays_days
        end_of_vacation_days = start_of_vacations_days + datetime.timedelta(days_for_delta2)
        vacations_delta = end_of_vacation_days - start_of_vacations_days

        list_of_potential_vacation_days = []

        for vacation_day in range(0,vacations_delta.days+1):
            list_of_potential_vacation_days.append(start_of_vacations_days + datetime.timedelta(vacation_day))

        copy_list_of_potential_vacation_days = list_of_potential_vacation_days.copy()

        if work_years == 1:
            start_of_vacations_days_for_check = request.user.date_joined.date() + \
                datetime.timedelta(days=days_for_delta) - datetime.timedelta(days=182)
            days_for_delta3 = year_days+all_holidays_days
            end_of_vacation_days = start_of_vacations_days_for_check + \
                datetime.timedelta(days_for_delta3) + datetime.timedelta(days=182)
            vacations_delta2 = end_of_vacation_days - start_of_vacations_days_for_check
            list_of_potential_vacation_days_for_check = []

            for vacation_day in range(0,vacations_delta2.days+1):
                list_of_potential_vacation_days_for_check.append(start_of_vacations_days_for_check + \
                    datetime.timedelta(vacation_day))
        
        else:
            start_of_vacations_days_for_check = request.user.date_joined.date() + datetime.timedelta(days=days_for_delta)
            days_for_delta3 = year_days+all_holidays_days
            end_of_vacation_days = start_of_vacations_days_for_check + datetime.timedelta(days_for_delta3) + datetime.timedelta(days=182)
            vacations_delta2 = end_of_vacation_days - start_of_vacations_days_for_check
            list_of_potential_vacation_days_for_check = []

            for vacation_day in range(0,vacations_delta2.days+1):
                list_of_potential_vacation_days_for_check.append(start_of_vacations_days_for_check + datetime.timedelta(vacation_day))

        list_of_used_vacation_days = []
        user_vacations = Vacation.objects.filter(user = request.user)
        for vacation in user_vacations:
            delta2 = vacation.vacation_end - vacation.vacation_start
            if delta2.days != 0:
                for b in range(0,delta2.days+1):
                    temp = vacation.vacation_start + datetime.timedelta(b)
                    if temp in list_of_potential_vacation_days_for_check:
                        list_of_used_vacation_days.append(temp)
                        try:
                            copy_list_of_potential_vacation_days.remove(temp)
                        except:
                            pass
        
            else:
                if vacation.vacation_start.date() in list_of_potential_vacation_days_for_check:
                    list_of_used_vacation_days.append(temp)
                    try:
                        copy_list_of_potential_vacation_days.remove(temp)
                    except:
                        pass

        vacation_days = potential_vacation_days - len(list_of_used_vacation_days)
    
    context.update({"vacation_days":vacation_days})
    alert_text = "Укажите дату!"
    
    return render(request, 'user_error_action.html', {'context': context , 'alert_text':alert_text, 'vacation_days':vacation_days})

def add_vacation(request):
    if request.method == 'POST':
    
        #Определяем пользователя, кто берет отпуск
        user = request.user
    
        #Определяем дату начала и на сколько берется отпуск
        vacation_start_str = request.POST['date']
        count_day_vacation = request.POST['Radios']
        if vacation_start_str == "":
            return redirect('user_panel_error')
        vacation_start = datetime.datetime.strptime(vacation_start_str, '%Y-%m-%d')
        vacation_end = vacation_start + datetime.timedelta(int(count_day_vacation)-1)
    
        #Заносим взятые даты в отдельный список, чтобы чекнуть правильность взятия дат
        new_vacation_days = []
        delta_vac = vacation_end - vacation_start
        for day2 in range(0,delta_vac.days + 1):
            new_vacation_days.append(vacation_start + datetime.timedelta(day2))
    
        #Считаем количество праздников, которые выпадают на взятый отпуск
        add_holiday = check_holiday(vacation_start, vacation_end)
    
        #Начинаем формировать контекст для передачи инфы в html
        context = {request.user.username : {}}

        delta = datetime.date.today()-request.user.date_joined.date()
    
        #Считаем - сколько дней отпуска всего было взято пользователем
        count_vac_days = str(view_vacations(request.user.id, request.user.date_joined.date(), datetime.date.today()))
    
        #Считаем - сколько дней было отработано пользователем на сегодняшний день и заносим в контекст вместе с другой информацией из БД
        work_days = calc_work_days(request.user.id)
        work_days_context = {"work_days":work_days}

        vacations = Vacation.objects.filter(user = request.user).order_by('vacation_start')
        out_offs = OutOffice.objects.filter(user = request.user).order_by('out_office_start')
        dayoffs = DayOff.objects.filter(user = request.user).order_by('day_off_start')
        sicks = Sick.objects.filter(user = request.user).order_by('sick_start')
    
        context.update(work_days_context)
        context.update({"vac_days":vacations})
        context.update({"off_days":dayoffs})
        context.update({"out_days":out_offs})
        context.update({"sick_days":sicks})
        context.update({"count_vac_days":count_vac_days})

        #Считаем количество праздников в году
        all_holidays = Holiday.objects.all()
        all_holidays_days = 0
        for holiday in all_holidays:
            all_holidays_days += holiday.calc_days()

        half_year = 183
        half_vac_days = 14
        year_days = 365
    
        #Сколько можно взять дней максимум
        potential_vacation_days = 28
    
        #Сколько можно взять дней
        vacation_days = 0
        if work_days < half_year :
            alert_text = "Нет свободных дней отпуска!"
            all_user_vac_days = view_vacations(request.user.id, request.user.date_joined.date(), datetime.date.today())
            new_vac =  HolidayVacation.objects.filter(user = request.user).order_by('vac_start')
            context.update({"new_vac_days":new_vac})

            return render(request, 'user_error_action.html', {'context': context, 'alert_text':alert_text, "vacation_days":vacation_days})

        #Если отработано больше 182, но меньше 365
        elif work_days >= half_year and  work_days < year_days:

            start_of_vacations_days = request.user.date_joined.date() +  datetime.timedelta(half_year)
            end_of_vacation_days = start_of_vacations_days + datetime.timedelta(year_days+all_holidays_days)

            vacations_delta = end_of_vacation_days - start_of_vacations_days

            #Список всех дней, которые можно взять
            list_of_potential_vacation_days = []

            for vacation_day in range(0,vacations_delta.days+1):
                list_of_potential_vacation_days.append(start_of_vacations_days + datetime.timedelta(vacation_day))

            #Список всех дней, которые можно взять с учётом взятых отпусков в этом году
            copy_list_of_potential_vacation_days = list_of_potential_vacation_days.copy()
            list_of_used_vacation_days = []
            user_vacations = Vacation.objects.filter(user = request.user)
            for vacation in user_vacations:
                delta2 = vacation.vacation_end - vacation.vacation_start
                if delta2.days != 0:
                    for b in range(0,delta2.days+1):
                        temp = vacation.vacation_start + datetime.timedelta(b)
                        if temp in list_of_potential_vacation_days:
                            list_of_used_vacation_days.append(temp)
                            copy_list_of_potential_vacation_days.remove(temp)
                else:
                    if vacation.vacation_start.date() in list_of_potential_vacation_days:
                        list_of_used_vacation_days.append(temp)
                        copy_list_of_potential_vacation_days.remove(temp)

            #Количество дней, которые пользователь может взять в качестве отпуска за этот год
            vacation_days = half_vac_days - len(list_of_used_vacation_days)
            if vacation_days == 0 :
                alert_text = "Нет свободных дней отпуска!"
                all_user_vac_days = view_vacations(request.user.id, request.user.date_joined.date(), datetime.date.today())
                new_vac =  HolidayVacation.objects.filter(user = request.user).order_by('vac_start')
                context.update({"new_vac_days":new_vac})

                return render(request, 'user_error_action.html', {'context': context, 'alert_text':alert_text, "vacation_days":vacation_days})

            #Если свободных дней не хватает
            elif vacation_days < delta_vac.days+1:
                alert_text = "Не хватает свободных дней отпуска!"
                all_user_vac_days = view_vacations(request.user.id, request.user.date_joined.date(), datetime.date.today())
                new_vac =  HolidayVacation.objects.filter(user = request.user).order_by('vac_start')
                context.update({"new_vac_days":new_vac})

                return render(request, 'user_error_action.html', {'context': context, 'alert_text':alert_text, "vacation_days":vacation_days})

            #Если свободных дней хватает
            else:

                #Считаем количество 7-дневных отпусков, взятых за год (д.быть не более 2х)
                count_7_days_vacs = calc_7_days_vacations(user.id,start_of_vacations_days,end_of_vacation_days)
                if (int(count_7_days_vacs) >=2 and int(count_day_vacation) == 7):
                    alert_text = "Вы можете взять только 14-дневный отпуск!"
                    new_vac =  HolidayVacation.objects.filter(user = request.user).order_by('vac_start')
                    context.update({"new_vac_days":new_vac})
                    return render(request, 'user_error_action.html', {'context': context, 'alert_text':alert_text, "vacation_days":vacation_days})

                #Если всё удовлетворяет
                else:
                    delta_now = datetime.date.today() - start_of_vacations_days
                    for day in range(0,delta_now.days + 1):
                        try:
                            copy_list_of_potential_vacation_days.remove(start_of_vacations_days + datetime.timedelta(day))
                        except:
                            pass

                    #Проверяем новый отпуск на дни, которые были взяты и дни, которые не входят в рабочий год,
                    # за который можно брать (т.е. берется раньше нужного или позже нужного)
                    for new_vacation_day in new_vacation_days:
                        if new_vacation_day.date() not in copy_list_of_potential_vacation_days:
                            alert_text = "Скорректируете дату отпуска!"
                            new_vac =  HolidayVacation.objects.filter(user = request.user).order_by('vac_start')
                            context.update({"new_vac_days":new_vac})

                            return render(request, 'user_error_action.html', {'context': context, 'alert_text':alert_text, "vacation_days":vacation_days})

                    #Добавление отпуска
                    vacation = Vacation(user = user, vacation_start = vacation_start, vacation_end = vacation_end)
                    vacation.save()

                    #Добавление отпуска с учётом праздников
                    holiday_vac = HolidayVacation(user = user, vacation = vacation, vac_start = vacation_start,
                        count_holiday = add_holiday, new_vacation_end = vacation_end  + datetime.timedelta(add_holiday))
                    holiday_vac.save()

                    #Отображение всех взятых отпусков пользователя с учётом взятого сейчас
                    new_vac =  HolidayVacation.objects.filter(user = user).order_by('vac_start')
                    context.update({"new_vac_days":new_vac})
                    alert_text = "Отпуск добавлен!"

                    #Подсчёт дней всех взятых отпусков
                    new_vacation_days = str(view_vacations(user.id, request.user.date_joined.date(), datetime.date.today()))
                    context.update({"count_vac_days":new_vacation_days})
                    delta = vacation.vacation_end - vacation.vacation_start
                    vacation_days = vacation_days - delta.days - 1

                    head_mail = "Планирование отпуска"
                    body_mail = "Внимание! " + str(request.user.last_name) + " " +  str(request.user.last_name)  + \
                        " запланировал отпуск на следующие даты: c " + \
                        str(holiday_vac.vac_start.strftime("%d.%m.%Y")) + " по " + \
                        str(holiday_vac.new_vacation_end.strftime("%d.%m.%Y")) + \
                        "."

                    from_mail = EMAIL_HOST_USER
                    to_mail = list()
                    to_mail.append(EMAIL_HOST_USER)
                    send_mail(head_mail, body_mail, from_mail, to_mail)
                    return render(request, 'user_success_action.html', {'context': context,
                        'alert_text':alert_text, "vacation_days":vacation_days})

        #Если отработано больше 365, то можно
        else:

            #Количество полных отработанных лет
            count_of_work_years = work_days/year_days
            work_years = floor(count_of_work_years)

            #Это количество отработанных лет переводится в количество дней, чтобы отсчитать день, с которого можно брать отпуска за прошлый рабочий год
            days_for_delta = work_years * (year_days + all_holidays_days)

            #Первый день, с которого можно брать отпуск
            start_of_vacations_days = request.user.date_joined.date() + datetime.timedelta(days=days_for_delta)

            #Последний день, до которого можно брать отпуск
            end_of_vacation_days = start_of_vacations_days + datetime.timedelta(year_days+all_holidays_days)

            #Разница
            vacations_delta = end_of_vacation_days - start_of_vacations_days

            #Список всех дней, которые можно взять
            list_of_potential_vacation_days = []

            for vacation_day in range(0,vacations_delta.days+1):
                list_of_potential_vacation_days.append(start_of_vacations_days + datetime.timedelta(vacation_day))

            #Список всех дней, которые можно взять с учётом взятых отпусков в этом году
            copy_list_of_potential_vacation_days = list_of_potential_vacation_days.copy()
            list_of_used_vacation_days = []
            user_vacations = Vacation.objects.filter(user = request.user)
            for vacation in user_vacations:
                delta2 = vacation.vacation_end - vacation.vacation_start
                if delta2.days != 0:
                    for b in range(0,delta2.days+1):
                        temp = vacation.vacation_start + datetime.timedelta(b)
                        if temp in list_of_potential_vacation_days:
                            list_of_used_vacation_days.append(temp)
                            copy_list_of_potential_vacation_days.remove(temp)
                else:
                    if vacation.vacation_start.date() in list_of_potential_vacation_days:
                        list_of_used_vacation_days.append(temp)
                        copy_list_of_potential_vacation_days.remove(temp)

            #Количество дней, которые пользователь может взять в качестве отпуска за этот год
            vacation_days = potential_vacation_days - len(list_of_used_vacation_days)

            #Если свободных дней нет
            if vacation_days == 0 :
                alert_text = "Нет свободных дней отпуска!"
                all_user_vac_days = view_vacations(request.user.id, request.user.date_joined.date(), datetime.date.today())
                new_vac =  HolidayVacation.objects.filter(user = request.user).order_by('vac_start')
                context.update({"new_vac_days":new_vac})

                return render(request, 'user_error_action.html', {'context': context, 'alert_text':alert_text, "vacation_days":vacation_days})

            #Если свободных дней не хватает
            elif vacation_days < delta_vac.days+1:
                alert_text = "Не хватает свободных дней отпуска!"
                all_user_vac_days = view_vacations(request.user.id, request.user.date_joined.date(), datetime.date.today())
                new_vac =  HolidayVacation.objects.filter(user = request.user).order_by('vac_start')
                context.update({"new_vac_days":new_vac})
                return render(request, 'user_error_action.html', {'context': context, 'alert_text':alert_text, "vacation_days":vacation_days})

            #Если свободных дней хватает
            else:

                #Считаем количество 7-дневных отпусков, взятых за год (д.быть не более 2х)
                count_7_days_vacs = calc_7_days_vacations(user.id,start_of_vacations_days,end_of_vacation_days)
                if (int(count_7_days_vacs) >=2 and int(count_day_vacation) == 7):
                    alert_text = "Вы можете взять только 14-дневный отпуск!"
                    new_vac =  HolidayVacation.objects.filter(user = request.user).order_by('vac_start')
                    context.update({"new_vac_days":new_vac})
                    return render(request, 'user_error_action.html', {'context': context, 'alert_text':alert_text, "vacation_days":vacation_days})

                #Если всё удовлетворяет
                else:
                    delta_now = datetime.date.today() - start_of_vacations_days
                    for day in range(0,delta_now.days + 1):
                        try:
                            copy_list_of_potential_vacation_days.remove(start_of_vacations_days + datetime.timedelta(day))
                        except:
                            pass

                    #Проверяем новый отпуск на дни, которые были взяты и дни, которые не входят в рабочий год,
                    # за который можно брать (т.е. берется раньше нужного или позже нужного)
                    for new_vacation_day in new_vacation_days:
                        if new_vacation_day.date() not in copy_list_of_potential_vacation_days:
                            alert_text = "Скорректируете дату отпуска!"
                            new_vac =  HolidayVacation.objects.filter(user = request.user).order_by('vac_start')
                            context.update({"new_vac_days":new_vac})

                            return render(request, 'user_error_action.html', {'context': context, 'alert_text':alert_text, "vacation_days":vacation_days})

                    #Добавление отпуска
                    vacation = Vacation(user = user, vacation_start = vacation_start, vacation_end = vacation_end)
                    vacation.save()

                    #Добавление отпуска с учётом праздников
                    holiday_vac = HolidayVacation(user = user, vacation = vacation, vac_start = vacation_start,
                        count_holiday = add_holiday, new_vacation_end = vacation_end  + datetime.timedelta(add_holiday))
                    
                    holiday_vac.save()

                    #Отображение всех взятых отпусков пользователя с учётом взятого сейчас
                    new_vac =  HolidayVacation.objects.filter(user = user).order_by('vac_start')
                    context.update({"new_vac_days":new_vac})
                    alert_text = "Отпуск добавлен!"
                    
                    #Подсчёт дней всех взятых отпусков
                    new_vacation_days = str(view_vacations(user.id, request.user.date_joined.date(), datetime.date.today()))
                    context.update({"count_vac_days":new_vacation_days})
                    delta = vacation.vacation_end - vacation.vacation_start
                    vacation_days = vacation_days - delta.days - 1


                    head_mail = "Планирование отпуска"
                    body_mail = "Внимание! " + str(request.user.last_name) + " " +  str(request.user.last_name)  + \
                        " запланировал отпуск на следующие даты: c " + \
                        str(holiday_vac.vac_start.strftime("%d.%m.%Y")) + " по " + \
                        str(holiday_vac.new_vacation_end.strftime("%d.%m.%Y")) + \
                        "."

                    from_mail = EMAIL_HOST_USER
                    to_mail = list()
                    to_mail.append(EMAIL_HOST_USER)
                    send_mail(head_mail, body_mail, from_mail, to_mail)

                    return render(request, 'user_success_action.html', {'context': context, 'alert_text':alert_text, "vacation_days":vacation_days})


def add_sick(request):
    if request.method == 'POST':
        sick_start_str = request.POST['date1']
        sick_end_str = request.POST['date2']
        
        if sick_start_str == '':
            return redirect('user_panel_error')
        
        elif sick_end_str == '':
            sick_start = datetime.datetime.strptime(sick_start_str, '%Y-%m-%d')
            sick = Sick(user = request.user, sick_start = sick_start, sick_end = sick_start)
            sick.save()
        
        else:
            sick_start = datetime.datetime.strptime(sick_start_str, '%Y-%m-%d')
            sick_end = datetime.datetime.strptime(sick_end_str, '%Y-%m-%d')
            sick = Sick(user = request.user, sick_start = sick_start, sick_end = sick_end)
            sick.save()
        
        return redirect('user_panel')

def add_day_off(request):
    if request.method == 'POST':
        day_off_start_str = request.POST['date1']
        day_off_end_str = request.POST['date2']
        
        if day_off_start_str == '':
            return redirect('user_panel_error')
        
        elif day_off_end_str == '':
            day_off_start = datetime.datetime.strptime(day_off_start_str, '%Y-%m-%d')
            day_off = DayOff(user = request.user, day_off_start = day_off_start, day_off_end = day_off_start)
            day_off.save()
        
        else:
            day_off_start = datetime.datetime.strptime(day_off_start_str, '%Y-%m-%d')
            day_off_end = datetime.datetime.strptime(day_off_end_str, '%Y-%m-%d')
            day_off = DayOff(user = request.user, day_off_start = day_off_start, day_off_end = day_off_end)
            day_off.save()
        
        return redirect('user_panel')

def add_out_office(request):
    if request.method == 'POST':
        out_office_start_str = request.POST['date1']
        out_office_end_str = request.POST['date2']
        
        if out_office_start_str == '':
            return redirect('user_panel_error')
        
        if out_office_end_str == '':
            out_office_start = datetime.datetime.strptime(out_office_start_str, '%Y-%m-%d')
            out_office = OutOffice(user = request.user, out_office_start = out_office_start, out_office_end = out_office_start)
            out_office.save()
        
        else:
            out_office_start = datetime.datetime.strptime(out_office_start_str, '%Y-%m-%d')
            out_office_end = datetime.datetime.strptime(out_office_end_str, '%Y-%m-%d')
            out_office = OutOffice(user = request.user, out_office_start = out_office_start, out_office_end = out_office_end)
            out_office.save()
        
        return redirect('user_panel')

def delete_sick(request):
    if request.method == 'POST':
        for key in request.POST.keys():
            if request.POST[key] == 'х':
                sick = Sick.objects.get(id=key)
                sick.delete()
        return redirect('user_panel')

def delete_day_off(request):
    if request.method == 'POST':
        for key in request.POST.keys():
            if request.POST[key] == 'х':
                day_off = DayOff.objects.get(id=key)
                day_off.delete()

        return redirect('user_panel')

def delete_out_office(request):
    if request.method == 'POST':
        for key in request.POST.keys():
            if request.POST[key] == 'х':
                out_office = OutOffice.objects.get(id=key)
                out_office.delete()
        return redirect('user_panel')

def vacations_list(request):
    if request.method == 'POST':
        context = {}
        try:
            if 'Все сотрудники' in request.POST.getlist('combo-name'):
                users_with_admin = User.objects.all().order_by('last_name')
                users = []
                for us in users_with_admin:
                    if not us.is_staff:
                        users.append(us)
               
                for user in users:
                    first_name = {"first_name":user.first_name}
                    last_name = {"last_name":user.last_name}
                    delta = datetime.date.today()-user.date_joined.date()
                    work_days2 = calc_work_days(user.id)
                    work_days = {"work_days":work_days2}
                    
                    vacations = Vacation.objects.filter(user = user)
                    vacs = []
                    for vac in vacations:
                        if vac.vacation_start == vac.vacation_end:
                            vacs.append(str(vac.vacation_start.strftime("%d.%m.%Y")))
                        else:
                            vacs.append("с " + str(vac.vacation_start.strftime("%d.%m.%Y")) + " по " + str(vac.vacation_end.strftime("%d.%m.%Y")) )
                    vac_days = {"vac_days": vacs}

                    count_vac_days = str(view_vacations(user.id, user.date_joined.date(), datetime.date.today()))
                    new_vac =  HolidayVacation.objects.filter(user = user).order_by('vac_start')

                    context[user.username] = last_name
                    context[user.username].update({"new_vac": new_vac})
                    context[user.username].update(first_name)
                    context[user.username].update(work_days)
                    context[user.username].update(vac_days)
                    context[user.username].update({"count_vac_days":count_vac_days})
                return render(request, 'user_vacations.html', {'context': context, 'users': users})
            
            else:
                users_with_admin = User.objects.all().order_by('last_name')
                users = []
                for us in users_with_admin:
                    if not us.is_staff:
                        users.append(us)
                
                names = request.POST.getlist('combo-name')
                
                users_combo = []
                for name in names:
                    user_combo = User.objects.get(username = name)
                    users_combo.append(user_combo)

                dict_with_combo_users = {}
                for user_combo in users_combo:
                    username = user_combo.username
                    dict_with_combo_users[username] = {"first_name":user_combo.first_name}
                    dict_with_combo_users[username].update({"last_name":user_combo.last_name})
                    
                    vacations = Vacation.objects.filter(user = user_combo)
                    vacs = []
                    for vac in vacations:
                        if vac.vacation_start == vac.vacation_end:
                            vacs.append(str(vac.vacation_start.strftime("%d.%m.%Y")))
                        else:
                            vacs.append("с " + str(vac.vacation_start.strftime("%d.%m.%Y")) + " по " + str(vac.vacation_end.strftime("%d.%m.%Y")) )
                    
                    dict_with_combo_users[username].update({"vac_days": vacs})
                    count_vac_days = str(view_vacations(user_combo.id, user_combo.date_joined.date(), datetime.date.today()))
                    new_vac =  HolidayVacation.objects.filter(user = user_combo).order_by('vac_start')
                    dict_with_combo_users[username].update({"new_vac": new_vac})
                    dict_with_combo_users[username].update({"count_vac_days":count_vac_days})
                
                return render(request, 'user_vacations.html', {'context': dict_with_combo_users, 'users': users})
        
        except:
            users_with_admin = User.objects.all().order_by('last_name')
            users = []
            for us in users_with_admin:
                if not us.is_staff:
                    users.append(us)
            names = request.POST.getlist('combo-name')
            users_combo = []
            for name in names:
                user_combo = User.objects.get(username = name)
                users_combo.append(user_combo)

            dict_with_combo_users = {}
            for user_combo in users_combo:
                username = user_combo.username
                dict_with_combo_users[username] = {"first_name":user_combo.first_name}
                dict_with_combo_users[username].update({"last_name":user_combo.last_name})
                
                vacations = Vacation.objects.filter(user = user_combo)
                vacs = []
                for vac in vacations:
                    if vac.vacation_start == vac.vacation_end:
                        vacs.append(str(vac.vacation_start.strftime("%d.%m.%Y")))
                    else:
                        vacs.append("с " + str(vac.vacation_start.strftime("%d.%m.%Y")) + " по " + str(vac.vacation_end.strftime("%d.%m.%Y")) )
                
                dict_with_combo_users[username].update({"vac_days": vacs})
                count_vac_days = str(view_vacations(user_combo.id, user_combo.date_joined.date(), datetime.date.today()))
                new_vac =  HolidayVacation.objects.filter(user = user_combo).order_by('vac_start')
                dict_with_combo_users[username].update({"new_vac": new_vac})
                dict_with_combo_users[username].update({"count_vac_days":count_vac_days})
            return render(request, 'user_vacations.html', {'context': dict_with_combo_users, 'users': users})


    if request.method == 'GET':
        context = {}
        users_with_admin = User.objects.all().order_by('last_name')
        users = []
        for us in users_with_admin:
            if not us.is_staff:
                users.append(us)
        
        for user in users:
            first_name = {"first_name":user.first_name}
            last_name = {"last_name":user.last_name}
            delta = datetime.date.today()-user.date_joined.date()
            work_days2 = calc_work_days(user.id)
            work_days = {"work_days":work_days2}
            vacations = Vacation.objects.filter(user = user)
            vacs = []
            for vac in vacations:
                if vac.vacation_start == vac.vacation_end:
                    vacs.append(str(vac.vacation_start.strftime("%d.%m.%Y")))
                else:
                    vacs.append("с " + str(vac.vacation_start.strftime("%d.%m.%Y")) + " по " + str(vac.vacation_end.strftime("%d.%m.%Y")) )
            vac_days = {"vac_days": vacs}

            count_vac_days = str(view_vacations(user.id, user.date_joined.date(), datetime.date.today()))

            new_vac =  HolidayVacation.objects.filter(user = user).order_by('vac_start')

            context[user.username] = last_name
            context[user.username].update({"new_vac": new_vac})
            context[user.username].update(first_name)
            context[user.username].update(work_days)
            context[user.username].update(vac_days)
            context[user.username].update({"count_vac_days":count_vac_days})
        
        return render(request, 'user_vacations.html', {'context': context, 'users': users})


def calc_7_days_vacations(user_id,start_day,end_day):
    user = User.objects.get(id = user_id)
    delta = end_day - start_day
    count_7_days_vacs = 0
    for day in range(0,delta.days+1):
        try:
            vacation = Vacation.objects.get(user=user, vacation_start = start_day + datetime.timedelta(day))
            if vacation.get_vacation_days() == 7:
                count_7_days_vacs += 1
        except:
            continue
    return count_7_days_vacs
