from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

from .models import *

User = get_user_model()

class UserRegistrationForm(forms.ModelForm):

    class Meta:
            model = User
            fields = ('last_name','first_name','email','username', 'password',)
            labels  = {
                'last_name': 'Фамилия',
                'first_name': 'Имя',
                'email': 'Почта',
                'username': 'Логин',
                'password':'Пароль'
            }
            
            widgets = {
                'last_name' : forms.TextInput(
                attrs= {
                'class' : 'form-control'
                }),

                'first_name' : forms.TextInput(
                attrs= {
                    'class' : 'form-control'
                }),

                'email' : forms.EmailInput(
                attrs= {
                    'class' : 'form-control'
                }),

                'username' : forms.TextInput(
                attrs= {
                    'class' : 'form-control'
                }),

                'password' : forms.PasswordInput(
                attrs= {
                    'class' : 'form-control'
                }
                )
            }

            help_texts = {
                'username' : "",
                'first_name' : "",
                'email' : "",
                'username' : "",
                'password' : ""
            }

class HolidayAddForm(forms.ModelForm):
    
    class Meta:
            model = Holiday
            fields = ('name','holiday_start','holiday_end')
            labels  = {
                'name': 'Название',
                'holiday_start': 'Дата начала праздника',
                'holiday_end': 'Дата окончания праздника'
                }