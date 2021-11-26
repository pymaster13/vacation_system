from django import forms

class UserLoginForm(forms.Form):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs= {'class' : 'form-control'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs= {'class' : 'form-control'}))

class UserLoginEmailForm(forms.Form):
    email = forms.CharField(label='Email', widget=forms.EmailInput(attrs= {'class' : 'form-control'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs= {'class' : 'form-control'}))
