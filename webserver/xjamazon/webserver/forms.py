from django import forms
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
import re


class BuyProductForm(forms.Form):
    item_id = forms.CharField(label='Item ID', max_length=20)
    ups_name = forms.CharField(label='UPS name', max_length=30)
    description = forms.CharField(label='Description', max_length=200)
    count = forms.IntegerField(label='Count', validators=[MaxValueValidator(999999),MinValueValidator(1)])
    x = forms.IntegerField(label='x')
    y = forms.IntegerField(label='y')


class WarehouseForm(forms.Form):
    whID = forms.CharField(label='Warehouse ID', max_length=20)
    x = forms.IntegerField(label='x')
    y = forms.IntegerField(label='y')


class LoginForm(forms.Form):
    username = forms.CharField(label='Username', max_length=40)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    # set rules for validation

    def clean_username(self):
        username = self.cleaned_data.get('username')
        filter_result = User.objects.filter(username__exact=username)
        if not filter_result:
            raise forms.ValidationError("This username does not exist.")
        
        return username        

def email_check(email):
    pattern = re.compile(r"\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?")
    return re.match(pattern, email)


class RegistrationForm(forms.Form):
    username = forms.CharField(label='Username', max_length=40)
    first_name = forms.CharField(label='Firstname', max_length=30)
    last_name = forms.CharField(label='Lastname', max_length=30)
    email = forms.EmailField(label='Email')
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password Confirmation', widget=forms.PasswordInput)

    # set rules for validation

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if len(username) < 6:
            raise forms.ValidationError("Your username must be at least 6 characters.")
        elif len(username) > 40:
            raise forms.ValidationError("Your username should be less than 41 characters.")
        else:
            filter_result = User.objects.filter(username__exact=username)
            if len(filter_result) > 0:
                raise forms.ValidationError("Your username already exists.")
        
        return username

    def clean_name(self):
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')

        if len(first_name) > 30:
            raise forms.ValidationError("Your first name should be less than 31 characters.")
        elif len(last_name) > 30:
            raise forms.ValidationError("Your last name should be less than 31 characters.")
        
        return first_name

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if email_check(email):
            filter_result = User.objects.filter(email__exact=email)
            if len(filter_result) > 0:
                raise forms.ValidationError("Your email already exists.")
        else:
            raise forms.ValidationError("Please enter a valid email.")

        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')

        if len(password1) < 8:
            raise forms.ValidationError("Password should be at least 8 characters.")
        elif len(password1) > 20:
            raise forms.ValidationError("Password cannot exceed 20 characters.")
        
        return password1
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Password mismatch. Please enter again.")

        return password2
