from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _

class User(AbstractUser):
    """User model."""

    email = models.EmailField(_('email address'), blank=True, unique=True)

class Vacation(models.Model):
    # ОТПУСК

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usersVacation', verbose_name='Сотрудник')
    vacation_start = models.DateField(editable = True, verbose_name='Дата начала отпуска')
    vacation_end = models.DateField(editable = True, verbose_name='Дата конца отпуска')

    class Meta:
        verbose_name = 'Отпуск'
        verbose_name_plural = 'Отпуска'

    def __str__(self):
        return self.user.username

    def get_vacation_days(self):
        delta = self.vacation_end - self.vacation_start
        return delta.days + 1


class HolidayVacation(models.Model):
    # ОТПУСК C УЧЁТОМ ПРАЗДНИКОВ
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userVacation', verbose_name='Сотрудники', null = True, blank = True)
    vacation = models.ForeignKey(Vacation, on_delete=models.CASCADE, related_name='holidayVacation', verbose_name='Отпуска')
    vac_start = models.DateField(editable = True, verbose_name='Дата конца отпуска с учетом праздников', null = True, blank = True)
    new_vacation_end = models.DateField(editable = True, verbose_name='Дата конца отпуска с учетом праздников', null = True)
    count_holiday = models.IntegerField(default = 0, verbose_name='Количество праздничных дней')

    class Meta:
        verbose_name = 'Входящий праздник'
        verbose_name_plural = 'Входящие праздники'

    def __str__(self):
        return str(self.count_holiday)

    def get_vacation_date(self):
        vac = self.vacation
        start = str(vac.vacation_start)
        end = str(vac.vacation_end)
        date_str = "c " + start + " по " + end
        return date_str

    def get_vacation_days(self):
        delta = self.new_vacation_end - self.vacation_start
        return delta.days + 1

class OutOffice(models.Model):
    # ВНЕ ОФИСА
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usersOutOffice', verbose_name='Сотрудник')
    out_office_start = models.DateField(editable = True, verbose_name='Дата начала работы вне офиса')
    out_office_end = models.DateField(editable = True, verbose_name='Дата конца работы вне офиса')

    class Meta:
        verbose_name = 'Работа вне офиса'
        verbose_name_plural = 'Работы вне офиса'

    def __str__(self):
        return self.user.username


class DayOff(models.Model):
    # ОТГУЛ
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usersDayOff', verbose_name='Сотрудник')
    day_off_start = models.DateField(editable = True, verbose_name='Дата начала отгула')
    day_off_end = models.DateField(editable = True, verbose_name='Дата конца отгула')

    class Meta:
        verbose_name = 'Отгул'
        verbose_name_plural = 'Отгулы'

    def __str__(self):
        return self.user.username

class Sick(models.Model):
    # БОЛЬНИЧНЫЙ
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usersSick', verbose_name='Сотрудник')
    sick_start = models.DateField(editable = True, verbose_name='Дата начала больничного')
    sick_end = models.DateField(editable = True, verbose_name='Дата конца больничного')

    class Meta:
        verbose_name = 'Больничный'
        verbose_name_plural = 'Больничные'

    def __str__(self):
        return self.user.username
