import datetime

from django.db import models


class Holiday(models.Model):
    name = models.CharField(max_length = 128, verbose_name='Название праздника')
    holiday_start = models.DateField(editable = True, verbose_name='Дата начала праздника')
    holiday_end = models.DateField(editable = True, verbose_name='Дата конца праздника')

    class Meta:
        verbose_name = 'Праздник'
        verbose_name_plural = 'Праздники'

    def __str__(self):
        return self.name

    def calc_days(self):
        days = self.holiday_end - self.holiday_start + datetime.timedelta(1)
        return days.days
