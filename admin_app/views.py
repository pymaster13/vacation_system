import datetime
from math import floor

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import render, redirect

from vacation.settings import EMAIL_HOST_USER
from client.models import *
from .forms import UserRegistrationForm
from .models import *

User = get_user_model()

def admin_index(request):
    """
    Rendering admin page
    """
    
    return render(request, 'index.html', {})

def register(request):
    """
    Register of new user
    """

    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)

        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.username = user_form.cleaned_data['username']
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            new_user_form = UserRegistrationForm()
            return render(request, 'register_success.html', {'user_form': new_user_form})
        else:
            user_form = UserRegistrationForm()
            return render(request, 'register_fail.html', {'user_form': user_form})

    else:
        user_form = UserRegistrationForm()
        return render(request, 'register.html', {'user_form': user_form})

def holidays(request):
    """
    Function of updating holidays
    """

    if request.method == 'POST':
        data = request.POST
        holidays = Holiday.objects.all()
        for holiday in holidays:
            if holiday.name in data:
                del_holiday = Holiday.objects.get(name = holiday.name)
                del_holiday.delete()

        context = {}

        holidays = Holiday.objects.all().order_by('holiday_start')

        for holiday in holidays:
            if holiday.holiday_start == holiday.holiday_end:
                context[holiday.name] = holiday.holiday_start.strftime("%d.%m")
            else:
                context[holiday.name] = "с " + str(holiday.holiday_start.strftime("%d.%m")) + " по " + str(holiday.holiday_end.strftime("%d.%m"))
        return render(request, 'holidays.html', {'context': context})

    else:
        context = {}

        holidays = Holiday.objects.all().order_by('holiday_start')

        for holiday in holidays:
            if holiday.holiday_start == holiday.holiday_end:
                context[holiday.name] = holiday.holiday_start.strftime("%d.%m")
            else:
                context[holiday.name] = "с " + str(holiday.holiday_start.strftime("%d.%m")) + " по " + str(holiday.holiday_end.strftime("%d.%m"))
        return render(request, 'holidays.html', {'context': context})

def add_holiday(request):
    """
    Function of holiday adding
    """

    context = {}

    holidays = Holiday.objects.all().order_by('holiday_start')

    for holiday in holidays:
        if holiday.holiday_start == holiday.holiday_end:
            context[holiday.name] = holiday.holiday_start.strftime("%d.%m")
        else:
            context[holiday.name] = "с " + str(holiday.holiday_start.strftime("%d.%m")) + " по " + str(holiday.holiday_end.strftime("%d.%m"))

    if request.method == 'POST':

        if request.POST['holiday-name'] == "" or request.POST['date'] == "" or request.POST['date2'] == "":
            return render(request, 'holidays_error.html', {'context': context})
        name = request.POST['holiday-name']

        holiday_start_str = request.POST['date']
        holiday_end_str = request.POST['date2']
        holiday_start = datetime.datetime.strptime(holiday_start_str, '%Y-%m-%d')
        holiday_end = datetime.datetime.strptime(holiday_end_str, '%Y-%m-%d')
        if holiday_start > holiday_end:
            return render(request, 'holidays_error.html', {'context': context})

        holiday = Holiday(name = name, holiday_start = holiday_start, holiday_end = holiday_end)
        holiday.save()
        return redirect('holidays')

def staff_info(request):
    """
    Info about all vacations
    """

    if request.method == 'POST':
        data_keys = list(request.POST.keys())

        try:
            data_key = data_keys[1]
        except:
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
                vacations = HolidayVacation.objects.filter(user = user).order_by('-vac_start')

                vacs = []
                for vac in vacations:
                    if vac.vac_start == vac.new_vacation_end:
                        vacs.append(str(vac.vac_start.strftime("%d.%m.%Y")))
                    else:
                        vacs.append("с " + str(vac.vac_start.strftime("%d.%m.%Y")) + " по " + str(vac.new_vacation_end.strftime("%d.%m.%Y")) )

                vac_days = {"vac_days": vacs}
                out_offs = OutOffice.objects.filter(user = user).order_by('-out_office_start')
                outs = []

                for out in out_offs:
                    if out.out_office_start == out.out_office_end:
                        outs.append(str(out.out_office_start.strftime("%d.%m.%Y")))
                    else:
                        outs.append("с " + str(out.out_office_start.strftime("%d.%m.%Y")) + " по " + str(out.out_office_end.strftime("%d.%m.%Y")))
                out_days = {"out_days": outs}

                dayoffs = DayOff.objects.filter(user = user).order_by('-day_off_start')
                offs = []
                for off in dayoffs:
                    if off.day_off_start == off.day_off_end:
                        offs.append(str(off.day_off_start.strftime("%d.%m.%Y")))
                    else:
                        offs.append("с " + str(off.day_off_start.strftime("%d.%m.%Y"))  + " по " + str(off.day_off_end.strftime("%d.%m.%Y")))
                off_days = {"off_days": offs}

                sicks = Sick.objects.filter(user = user).order_by('-sick_start')
                sicks_list = []
                for sick in sicks:
                    if sick.sick_start == sick.sick_end:
                        sicks_list.append(str(sick.sick_start.strftime("%d.%m.%Y")))
                    else:
                        sicks_list.append("с " + str(sick.sick_start.strftime("%d.%m.%Y")) + " по " + str(sick.sick_end.strftime("%d.%m.%Y")))
                sick_days = {"sick_days": sicks_list}

                count_vac_days = str(view_vacations(user.id, user.date_joined.date(), datetime.date.today()))
                context[user.username] = last_name
                context[user.username].update(first_name)
                context[user.username].update(work_days)
                context[user.username].update(vac_days)
                context[user.username].update(out_days)
                context[user.username].update(off_days)
                context[user.username].update(sick_days)
                context[user.username].update({"count_vac_days":count_vac_days})

            return render(request, 'staff_info.html', {'context': context})

        data = data_key

        if "по" in data:
            username = data.split(" с ")[0]
            date_start_str = data.split(" по ")[0][-10:]
            vacation_start = datetime.datetime.strptime(date_start_str, '%d.%m.%Y')
            date_end_str = data.split(" по ")[1][:10]
            vacation_end = datetime.datetime.strptime(date_end_str, '%d.%m.%Y')
            user = User.objects.get(username=username)

        else:
            username = data.split(" ")[0]
            date_start_str = data.split(" ")[1]
            vacation_start = datetime.datetime.strptime(date_start_str, '%d.%m.%Y')
            vacation_end = vacation_start
            user = User.objects.get(username=username)

        if request.POST[data_key] == "х":
            add_holiday = check_holiday(vacation_start, vacation_end)
            day_end_2 = vacation_end
            holiday_vac = HolidayVacation.objects.get(user = user, vac_start = vacation_start.date(),
                 new_vacation_end = vacation_end)
            vac = Vacation.objects.get(user=user, vacation_start=vacation_start.date())
            holiday_vac.delete()
            vac.delete()

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
                vacations = HolidayVacation.objects.filter(user = user).order_by('-vac_start')
                vacs = []
                for vac in vacations:
                    if vac.vac_start == vac.new_vacation_end:
                        vacs.append(str(vac.vac_start.strftime("%d.%m.%Y")))
                    else:
                        vacs.append("с " + str(vac.vac_start.strftime("%d.%m.%Y")) + " по "
                             + str(vac.new_vacation_end.strftime("%d.%m.%Y")) )
                vac_days = {"vac_days": vacs}

                out_offs = OutOffice.objects.filter(user = user).order_by('-out_office_start')
                outs = []
                for out in out_offs:
                    if out.out_office_start == out.out_office_end:
                        outs.append(str(out.out_office_start.strftime("%d.%m.%Y")))
                    else:
                        outs.append("с " + str(out.out_office_start.strftime("%d.%m.%Y")) + " по " + str(out.out_office_end.strftime("%d.%m.%Y")))
                out_days = {"out_days": outs}

                dayoffs = DayOff.objects.filter(user = user).order_by('-day_off_start')
                offs = []
                for off in dayoffs:
                    if off.day_off_start == off.day_off_end:
                        offs.append(str(off.day_off_start.strftime("%d.%m.%Y")))
                    else:
                        offs.append("с " + str(off.day_off_start.strftime("%d.%m.%Y"))  + " по " + str(off.day_off_end.strftime("%d.%m.%Y")))
                off_days = {"off_days": offs}

                sicks = Sick.objects.filter(user = user).order_by('-sick_start')
                sicks_list = []
                for sick in sicks:
                    if sick.sick_start == sick.sick_end:
                        sicks_list.append(str(sick.sick_start.strftime("%d.%m.%Y")))
                    else:
                        sicks_list.append("с " + str(sick.sick_start.strftime("%d.%m.%Y")) + " по " + str(sick.sick_end.strftime("%d.%m.%Y")))
                sick_days = {"sick_days": sicks_list}

                count_vac_days = str(view_vacations(user.id, user.date_joined.date(), datetime.date.today()))

                context[user.username] = last_name
                context[user.username].update(first_name)
                context[user.username].update(work_days)
                context[user.username].update(vac_days)
                context[user.username].update(out_days)
                context[user.username].update(off_days)
                context[user.username].update(sick_days)
                context[user.username].update({"count_vac_days":count_vac_days})

            return render(request, 'staff_info_success_delete.html', {'context': context})

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
            vacations = HolidayVacation.objects.filter(user = user).order_by('-vac_start')
            vacs = []
            for vac in vacations:
                if vac.vac_start == vac.new_vacation_end:
                    vacs.append(str(vac.vac_start.strftime("%d.%m.%Y")))
                else:
                    vacs.append("с " + str(vac.vac_start.strftime("%d.%m.%Y")) + " по " + str(vac.new_vacation_end.strftime("%d.%m.%Y")) )
            vac_days = {"vac_days": vacs}

            out_offs = OutOffice.objects.filter(user = user).order_by('-out_office_start')
            outs = []
            for out in out_offs:
                if out.out_office_start == out.out_office_end:
                    outs.append(str(out.out_office_start.strftime("%d.%m.%Y")))
                else:
                    outs.append("с " + str(out.out_office_start.strftime("%d.%m.%Y")) + " по " + str(out.out_office_end.strftime("%d.%m.%Y")))
            out_days = {"out_days": outs}

            dayoffs = DayOff.objects.filter(user = user).order_by('-day_off_start')
            offs = []
            for off in dayoffs:
                if off.day_off_start == off.day_off_end:
                    offs.append(str(off.day_off_start.strftime("%d.%m.%Y")))
                else:
                    offs.append("с " + str(off.day_off_start.strftime("%d.%m.%Y"))  + " по " + str(off.day_off_end.strftime("%d.%m.%Y")))
            off_days = {"off_days": offs}

            sicks = Sick.objects.filter(user = user).order_by('-sick_start')
            sicks_list = []
            for sick in sicks:
                if sick.sick_start == sick.sick_end:
                    sicks_list.append(str(sick.sick_start.strftime("%d.%m.%Y")))
                else:
                    sicks_list.append("с " + str(sick.sick_start.strftime("%d.%m.%Y")) + " по " + str(sick.sick_end.strftime("%d.%m.%Y")))
            sick_days = {"sick_days": sicks_list}

            count_vac_days = str(view_vacations(user.id, user.date_joined.date(), datetime.date.today()))

            context[user.username] = last_name
            context[user.username].update(first_name)
            context[user.username].update(work_days)
            context[user.username].update(vac_days)
            context[user.username].update(out_days)
            context[user.username].update(off_days)
            context[user.username].update(sick_days)
            context[user.username].update({"count_vac_days":count_vac_days})

        return render(request, 'staff_info.html', {'context': context})

def admin_vacation_error(request):
    users_with_admin = User.objects.all().order_by('last_name')
    users = []
    for us in users_with_admin:
        if not us.is_staff:
            users.append(us)
            
    users_names = []
    selected = "Выберите сотрудника"
    for user in users:
        users_names.append(user.last_name + " " + user.first_name)
    
    if request.POST:
        if 'success' in request.POST:
            last_and_first_names = request.POST['combo-name'].split(' ')
            last_name = last_and_first_names[0]
            first_name = last_and_first_names[1]
            user = User.objects.get(first_name=first_name, last_name=last_name)
            
            day_start_str = request.POST['date']
            vacation_start = datetime.datetime.strptime(day_start_str, '%d-%m-%Y')
            day_end_str = request.POST['date2']
            vacation_end = datetime.datetime.strptime(day_end_str, '%d-%m-%Y')
            vac = Vacation(user = user, vacation_start = vacation_start, vacation_end = vacation_end)
            vac.save()
            
            add_holiday = check_holiday(vacation_start, vacation_end)
            holiday_vac = HolidayVacation(user = user, vacation = vac, vac_start = vacation_start, count_holiday = add_holiday, new_vacation_end = vacation_end  + datetime.timedelta(add_holiday))
            holiday_vac.save()
            
            head_mail = "Планирование отпуска"
            body_mail = "Внимание! Администратор запланировал Ваш отпуск на следующие даты: c " + \
                str(holiday_vac.vac_start.strftime("%d.%m.%Y")) + " по " + \
                str(holiday_vac.new_vacation_end.strftime("%d.%m.%Y")) + \
                "."

            from_mail= EMAIL_HOST_USER
            to_mail = list()
            to_mail.append(user.email)
            send_mail(head_mail, body_mail, from_mail, to_mail)

            return render(request, 'admin_vacation_success.html', {'users_names':users_names})

        if 'cancel' in request.POST:
            return render(request, 'admin_vacation.html', {'users_names':users_names, 'selected':selected})

        return render(request, 'admin_vacation.html', {'users_names':users_names, 'selected':selected})

def admin_vacation(request):
    """
    Function of adding vacation from admin page
    """

    selected = "Выберите сотрудника"
    value_date_1 = ""
    value_date_2 = ""
    vacation = ""
    users_with_admin = User.objects.all().order_by('last_name')
    users = []
    for us in users_with_admin:
        if not us.is_staff:
            users.append(us)

    users_names = []
    for user in users:
        users_names.append(user.last_name + " " + user.first_name)

    if request.POST:
        if request.POST['combo-name'] != "Выберите сотрудника":
            user_name = request.POST['combo-name']
            last_and_first_names = request.POST['combo-name'].split(' ')
            last_name = last_and_first_names[0]
            first_name = last_and_first_names[1]

            user = User.objects.get(first_name=first_name, last_name=last_name)
            day_start_str = request.POST['date']
            day_end_str = request.POST['date2']

            if day_start_str =="" or day_end_str == "":
                vacation = "Проверьте корректность ввода дат!"
                return render(request, 'admin_vacation_error_2.html', {'users_names':users_names,'vacation':vacation})

            vacation_start = datetime.datetime.strptime(day_start_str, '%Y-%m-%d')
            vacation_end = datetime.datetime.strptime(day_end_str, '%Y-%m-%d')

            if vacation_start > vacation_end:
                vacation = "Проверьте корректность ввода дат!"
                return render(request, 'admin_vacation_error_2.html', {'users_names':users_names,'vacation':vacation})

            #Заносим взятые даты в отдельный список, чтобы чекнуть правильность взятия дат
            new_vacation_days = []
            delta_vac = vacation_end - vacation_start
            for day2 in range(0,delta_vac.days + 1):
                new_vacation_days.append(vacation_start + datetime.timedelta(day2))

            #Считаем количество праздников, которые выпадают на взятый отпуск
            add_holiday = check_holiday(vacation_start, vacation_end)

            #Начинаем формировать контекст для передачи инфы в html
            context = {user.username : {}}

            delta = datetime.date.today()- user.date_joined.date()

            #Считаем - сколько дней отпуска всего было взято пользователем
            count_vac_days = str(view_vacations(user.id, user.date_joined.date(), datetime.date.today()))

            #Считаем - сколько дней было отработано пользователем на сегодняшний день и заносим в контекст вместе с другой информацией из БД
            work_days = calc_work_days(user.id)
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
            potential_vacation_days = 28
            vacation_days = 0
            user_work_days = calc_work_days(request.user.id)

            #Если отработано меньше 365, то нельзя взять отпуск
            if work_days < half_year :
                selected = last_name + " " + first_name
                value_date_1 = vacation_start.date().strftime('%d-%m-%Y')
                value_date_2 = vacation_end.date().strftime('%d-%m-%Y')
                vacation = "Нет свободных дней отпуска!"
                return render(request, 'admin_vacation_error.html', {'users_names':user_name, 'vacation':vacation,
                    'selected':selected, 'value_date_1':value_date_1, 'value_date_2':value_date_2})

            elif work_days >= half_year and  work_days < year_days:

                start_of_vacations_days = user.date_joined.date() +  datetime.timedelta(half_year)
                end_of_vacation_days = start_of_vacations_days + datetime.timedelta(year_days+all_holidays_days)
                vacations_delta = end_of_vacation_days - start_of_vacations_days

                #Список всех дней, которые можно взять
                list_of_potential_vacation_days = []

                for vacation_day in range(0,vacations_delta.days+1):
                    list_of_potential_vacation_days.append(start_of_vacations_days + datetime.timedelta(vacation_day))

                #Список всех дней, которые можно взять с учётом взятых отпусков в этом году
                copy_list_of_potential_vacation_days = list_of_potential_vacation_days.copy()

                list_of_used_vacation_days = []
                user_vacations = Vacation.objects.filter(user = user)
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
                if vacation_days == 0 :
                    selected = last_name + " " + first_name
                    value_date_1 = vacation_start.date().strftime('%d-%m-%Y')
                    value_date_2 = vacation_end.date().strftime('%d-%m-%Y')
                    vacation = "Нет свободных дней отпуска!"
                    return render(request, 'admin_vacation_error.html', {'users_names':user_name, 'vacation':vacation,
                        'selected':selected, 'value_date_1':value_date_1, 'value_date_2':value_date_2})

                #Если свободных дней меньше 0
                elif vacation_days < 0:
                    selected = last_name + " " + first_name
                    value_date_1 = vacation_start.date().strftime('%d-%m-%Y')
                    value_date_2 = vacation_end.date().strftime('%d-%m-%Y')
                    vacation = "У данного пользователя дней отпуска больше, чем положено!"
                    return render(request, 'admin_vacation_error.html', {'users_names':user_name, 'vacation':vacation,
                        'selected':selected, 'value_date_1':value_date_1, 'value_date_2':value_date_2})
                
                #Если свободных дней меньше взятых
                elif vacation_days < delta_vac.days+1:
                    selected = last_name + " " + first_name
                    value_date_1 = vacation_start.date().strftime('%d-%m-%Y')
                    value_date_2 = vacation_end.date().strftime('%d-%m-%Y')
                    vacation = "У данного пользователя не хватает дней отпуска!"
                    return render(request, 'admin_vacation_error.html', {'users_names':user_name, 'vacation':vacation,
                        'selected':selected, 'value_date_1':value_date_1, 'value_date_2':value_date_2})
                
                #Если свободных дней хватает
                else:
                    
                    #Считаем количество 7-дневных отпусков, взятых за год (д.быть не более 2х)
                    count_7_days_vacs = calc_7_days_vacations(user.id,start_of_vacations_days,end_of_vacation_days)
                    if (int(count_7_days_vacs) >=2 and int(delta_vac.days) == 6):
                        selected = last_name + " " + first_name
                        value_date_1 = vacation_start.date().strftime('%d-%m-%Y')
                        value_date_2 = vacation_end.date().strftime('%d-%m-%Y')
                        vacation = "Стандартная схема отпусков нарушена - количество 7-дневных отпусков будет превышено!"
                        return render(request, 'admin_vacation_error.html', {'users_names':user_name, 'vacation':vacation,
                            'selected':selected, 'value_date_1':value_date_1, 'value_date_2':value_date_2})
                    
                    #Если всё удовлетворяет
                    elif delta_vac.days == 6 or delta_vac.days == 13:
                        
                        #Проверяем новый отпуск на дни, которые были взяты и дни, которые не входят в рабочий год, 
                        # за который можно брать (т.е. берется раньше нужного или позже нужного)
                        for new_vacation_day in new_vacation_days:
                            if new_vacation_day.date() not in copy_list_of_potential_vacation_days:
                                selected = last_name + " " + first_name
                                value_date_1 = vacation_start.date().strftime('%d-%m-%Y')
                                value_date_2 = vacation_end.date().strftime('%d-%m-%Y')
                                vacation = "Дата отпуска выбрана некорректно - внимательно проверьте даты!"
                                return render(request, 'admin_vacation_error.html', {'value_date_1':value_date_1,
                                    'value_date_2':value_date_2,'users_names':users_names, 'vacation':vacation, 'selected':selected})
                        
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
                        context.update({"count_vac_days":new_vacation_days})
                        delta = vacation.vacation_end - vacation.vacation_start
                        vacation_days = vacation_days - delta.days - 1

                        head_mail = "Планирование отпуска"
                        body_mail = "Внимание! Администратор запланировал Ваш отпуск на следующие даты: c " + \
                            str(holiday_vac.vac_start.strftime("%d.%m.%Y")) + " по " + \
                            str(holiday_vac.new_vacation_end.strftime("%d.%m.%Y")) + \
                            "."

                        from_mail = EMAIL_HOST_USER
                        to_mail = list()
                        to_mail.append(EMAIL_HOST_USER)
                        send_mail(head_mail, body_mail, from_mail, to_mail)
                        
                        return render(request, 'admin_vacation_success.html', {'users_names':users_names})
                    
                    else:
                        selected = last_name + " " + first_name
                        value_date_1 = vacation_start.date().strftime('%d-%m-%Y')
                        value_date_2 = vacation_end.date().strftime('%d-%m-%Y')
                        vacation = "Выбрано нестандартное количество дней отпуска!"
                        return render(request, 'admin_vacation_error.html', {'value_date_1':value_date_1,
                            'value_date_2':value_date_2,'users_names':users_names, 'vacation':vacation, 'selected':selected})
            
            #Если отработано больше 365, то можно
            else:
                
                #Количество полных отработанных лет
                count_of_work_years = work_days/year_days
                work_years = floor(count_of_work_years)
                
                #Это количество отработанных лет переводится в количество дней, чтобы отсчитать день, с которого можно брать отпуска за прошлый рабочий год
                days_for_delta = work_years * (year_days + all_holidays_days)
                
                #Первый день, с которого можно брать отпуск
                start_of_vacations_days = user.date_joined.date() +  datetime.timedelta(days=days_for_delta)
                
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

                if work_years == 1:
                    start_of_vacations_days_for_check = request.user.date_joined.date() + \
                        datetime.timedelta(days=days_for_delta) - datetime.timedelta(days=182)
                    
                    days_for_delta3 = year_days+all_holidays_days
                    end_of_vacation_days = start_of_vacations_days_for_check + datetime.timedelta(days_for_delta3) + datetime.timedelta(days=182)
                    vacations_delta2 = end_of_vacation_days - start_of_vacations_days_for_check
                    list_of_potential_vacation_days_for_check = []

                    for vacation_day in range(0,vacations_delta2.days+1):
                        list_of_potential_vacation_days_for_check.append(start_of_vacations_days_for_check + datetime.timedelta(vacation_day))
                else:
                    start_of_vacations_days_for_check = request.user.date_joined.date() + datetime.timedelta(days=days_for_delta)
                    days_for_delta3 = year_days+all_holidays_days
                    end_of_vacation_days = start_of_vacations_days_for_check + datetime.timedelta(days_for_delta3) + datetime.timedelta(days=182)
                    vacations_delta2 = end_of_vacation_days - start_of_vacations_days_for_check
                    list_of_potential_vacation_days_for_check = []

                    for vacation_day in range(0,vacations_delta2.days+1):
                        list_of_potential_vacation_days_for_check.append(start_of_vacations_days_for_check + datetime.timedelta(vacation_day))

                list_of_used_vacation_days = []
                user_vacations = Vacation.objects.filter(user = user)
                
                for vacation in user_vacations:
                    delta2 = vacation.vacation_end - vacation.vacation_start
                    if delta2.days != 0:
                        for b in range(0,delta2.days+1):
                            temp = vacation.vacation_start + datetime.timedelta(b)
                            if temp in list_of_potential_vacation_days_for_check:
                                list_of_used_vacation_days.append(temp)
                                try:
                                    copy_list_of_potential_vacation_days.remove(start_of_vacations_days + datetime.timedelta(day))
                                except:
                                    pass
                    
                    else:
                        if vacation.vacation_start in list_of_potential_vacation_days_for_check:
                            list_of_used_vacation_days.append(vacation.vacation_start)
                            try:
                                copy_list_of_potential_vacation_days.remove(vacation.vacation_start)
                            except:
                                pass
                
                #Количество дней, которые пользователь может взять в качестве отпуска за этот год
                vacation_days = potential_vacation_days - len(list_of_used_vacation_days)
                
                #Если свободных дней нет
                if vacation_days == 0 :
                    selected = last_name + " " + first_name
                    value_date_1 = vacation_start.date().strftime('%d-%m-%Y')
                    value_date_2 = vacation_end.date().strftime('%d-%m-%Y')
                    vacation = "Нет свободных дней отпуска!"
                    return render(request, 'admin_vacation_error.html', {'users_names':user_name,
                        'vacation':vacation, 'selected':selected, 'value_date_1':value_date_1, 'value_date_2':value_date_2})

                #Если свободных дней меньше 0
                elif vacation_days < 0:
                    selected = last_name + " " + first_name
                    value_date_1 = vacation_start.date().strftime('%d-%m-%Y')
                    value_date_2 = vacation_end.date().strftime('%d-%m-%Y')
                    vacation = "У данного пользователя дней отпуска больше, чем положено!"
                    return render(request, 'admin_vacation_error.html', {'users_names':user_name,
                        'vacation':vacation, 'selected':selected, 'value_date_1':value_date_1, 'value_date_2':value_date_2})
                
                #Если свободных дней меньше взятых
                elif vacation_days < delta_vac.days+1:
                    selected = last_name + " " + first_name
                    value_date_1 = vacation_start.date().strftime('%d-%m-%Y')
                    value_date_2 = vacation_end.date().strftime('%d-%m-%Y')
                    vacation = "У данного пользователя не хватает дней отпуска!"
                    return render(request, 'admin_vacation_error.html', {'users_names':user_name, 'vacation':vacation,
                        'selected':selected, 'value_date_1':value_date_1, 'value_date_2':value_date_2})
                
                #Если свободных дней хватает
                else:
                    
                    #Считаем количество 7-дневных отпусков, взятых за год (д.быть не более 2х)
                    count_7_days_vacs = calc_7_days_vacations(user.id,start_of_vacations_days,end_of_vacation_days)
                    if (int(count_7_days_vacs) >=2 and int(delta_vac.days) == 6):
                        selected = last_name + " " + first_name
                        value_date_1 = vacation_start.date().strftime('%d-%m-%Y')
                        value_date_2 = vacation_end.date().strftime('%d-%m-%Y')
                        vacation = "Стандартная схема отпусков нарушена - количество 7-дневных отпусков будет превышено!"
                        return render(request, 'admin_vacation_error.html', {'users_names':user_name, 'vacation':vacation,
                            'selected':selected, 'value_date_1':value_date_1, 'value_date_2':value_date_2})
                    
                    #Если всё удовлетворяет
                    elif delta_vac.days == 6 or delta_vac.days == 13:
                        
                        #Проверяем новый отпуск на дни, которые были взяты и дни, которые не входят в рабочий год,
                        # за который можно брать (т.е. берется раньше нужного или позже нужного)
                        for new_vacation_day in new_vacation_days:
                            if new_vacation_day.date() not in copy_list_of_potential_vacation_days:
                                selected = last_name + " " + first_name
                                value_date_1 = vacation_start.date().strftime('%d-%m-%Y')
                                value_date_2 = vacation_end.date().strftime('%d-%m-%Y')
                                vacation = "Дата отпуска выбрана некорректно - внимательно проверьте даты!"
                                return render(request, 'admin_vacation_error.html', {'value_date_1':value_date_1,
                                    'value_date_2':value_date_2,'users_names':users_names, 'vacation':vacation, 'selected':selected})
                        
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
                        
                        return render(request, 'admin_vacation_success.html', {'users_names':users_names})
                    else:
                        selected = last_name + " " + first_name
                        value_date_1 = vacation_start.date().strftime('%d-%m-%Y')
                        value_date_2 = vacation_end.date().strftime('%d-%m-%Y')
                        vacation = "Выбрано нестандартное количество дней отпуска!"
                        return render(request, 'admin_vacation_error.html', {'value_date_1':value_date_1,
                            'value_date_2':value_date_2,'users_names':users_names, 'vacation':vacation, 'selected':selected})

        else:
            users_with_admin = User.objects.all().order_by('last_name')
            users = []
            for us in users_with_admin:
                if not us.is_staff:
                    users.append(us)

            users_names = []
            for user in users:
                users_names.append(user.last_name + " " + user.first_name)
            vacation = "Выберите сотрудника!"
            
            return render(request, 'admin_vacation_error_2.html', {'vacation':vacation, 'users_names':users_names})

    else:
        users_with_admin = User.objects.all().order_by('last_name')
        users = []
        for us in users_with_admin:
            if not us.is_staff:
                users.append(us)

        users_names = []
        for user in users:
            users_names.append(user.last_name + " " + user.first_name)

        return render(request, 'admin_vacation.html', {'users_names':users_names, 'vacation':vacation,
            'selected':selected, 'value_date_1':value_date_1, 'value_date_2':value_date_2})

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
    count_days = 0
    delta = date_end - date_start
    date_step = datetime.timedelta(1)
    date_list = []
    
    if date_start != date_end:
        for a in range(0,delta.days+1):
            temp = date_start + datetime.timedelta(a)
            date_list.append(temp.strftime("%d.%m"))
        for date in date_list:
            if date in holiday_list:
                count_days += 1
    else:
        if date_start.strftime("%d.%m") in holiday_list:
            count_days += 1
    
    return count_days

def check_vacations(user_id, date_start, date_end):
    count_days = 0
    user = User.objects.get(id = user_id)
    delta = date_end - date_start
    date_step = datetime.timedelta(1)
    date_list = []
    
    for a in range(1,delta.days+1):
        temp = date_start + datetime.timedelta(a)
        date_list.append(temp)
    
    vacations = Vacation.objects.filter(user = user)
    
    for vacation in vacations:
        delta2 = vacation.vacation_end - vacation.vacation_start
        if delta2.days != 0:
            for b in range(0,delta2.days+1):
                temp2 = vacation.vacation_start + datetime.timedelta(b)
                if temp2 in date_list:
                    count_days += 1
        else:
            temp3 = vacation.vacation_start
            if temp3 in date_list:
                count_days += 1
    
    return count_days

def view_vacations(user_id, date_start, date_end):
    count_days = 0
    user = User.objects.get(id = user_id)
    delta = date_end - date_start
    date_step = datetime.timedelta(1)
    date_list = []
    
    for a in range(1,delta.days+1):
        temp = date_start + datetime.timedelta(a)
        date_list.append(temp)
    
    vacations = Vacation.objects.filter(user = user)
    
    for vacation in vacations:
        delta2 = vacation.vacation_end - vacation.vacation_start
        if delta2.days != 0:
            for b in range(0,delta2.days+1):
                temp2 = vacation.vacation_start + datetime.timedelta(b)
                count_days += 1
        else:
            count_days += 1
    
    return count_days

def check_off_days(user_id, date_start, date_end):
    count_days = 0
    user = User.objects.get(id = user_id)
    delta = date_end - date_start
    date_step = datetime.timedelta(1)
    date_list = []
    
    for a in range(1,delta.days+1):
        temp = date_start + datetime.timedelta(a)
        date_list.append(temp)
    
    offs = DayOff.objects.filter(user = user)

    for off in offs:
        delta2 = off.day_off_end - off.day_off_start
        if delta2.days != 0:
            for b in range(1,delta2.days+1):
                temp2 = off.day_off_start + datetime.timedelta(b)
    
                if temp2 in date_list:
                    count_days += 1
    
                    if temp2 ==  off.day_off_end:
                        count_days += 1
        else:
            temp3 = off.day_off_start
            if temp3 in date_list:
                count_days += 1
    
    return count_days

def check_out_days(user_id, date_start, date_end):
    count_days = 0
    user = User.objects.get(id = user_id)
    delta = date_end - date_start
    date_step = datetime.timedelta(1)
    date_list = []
    for a in range(1,delta.days+1):
        temp = date_start + datetime.timedelta(a)
        date_list.append(temp)
    
    outs = OutOffice.objects.filter(user = user)

    for out in outs:
        delta2 = out.out_office_end - out.out_office_start
        if delta2.days != 0:
            for b in range(1,delta2.days+1):
                temp2 = out.out_office_start + datetime.timedelta(b)
    
                if temp2 in date_list:
                    count_days += 1
    
                    if temp2 ==  out.out_office_end:
                        count_days += 1
        else:
            temp3 = out.out_office_start
            if temp3 in date_list:
                count_days += 1
    
    return count_days


def check_sick_days(user_id, date_start, date_end):
    count_days = 0
    user = User.objects.get(id = user_id)
    delta = date_end - date_start
    date_step = datetime.timedelta(1)
    date_list = []
    for a in range(1,delta.days+1):
        temp = date_start + datetime.timedelta(a)
        date_list.append(temp)
    
    sicks = Sick.objects.filter(user = user)

    for sick in sicks:
        delta2 = sick.sick_end - sick.sick_start
        if delta2.days != 0:
            for b in range(1,delta2.days+1):
                temp2 = sick.sick_start + datetime.timedelta(b)
    
                if temp2 in date_list:
                    count_days += 1
    
                    if temp2 == sick.sick_end:
                        count_days += 1

        else:
            temp3 = sick.sick_start
            if temp3 in date_list:
                count_days += 1

    return count_days


def calc_work_days(user_id):
    user = User.objects.get(id = user_id)
    
    all_work = datetime.date.today() - user.date_joined.date() +  datetime.timedelta(days=1)
    number_holidays = check_holiday(user.date_joined.date(), datetime.date.today())
    number_vac_days = check_vacations(user.id, user.date_joined.date(), datetime.date.today())
    number_off_days = check_off_days(user.id, user.date_joined.date(), datetime.date.today())
    number_out_days = check_out_days(user.id, user.date_joined.date(), datetime.date.today())
    number_sick_days = check_sick_days(user.id, user.date_joined.date(), datetime.date.today())
    
    all_work_days = all_work.days
    work_days = all_work_days - number_holidays - number_vac_days - number_off_days -\
                number_out_days - number_sick_days
    
    return work_days

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
