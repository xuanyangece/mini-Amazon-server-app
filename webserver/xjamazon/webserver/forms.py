from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator

class BuyForm(forms.Form):
    item_id = forms.CharField(label='Item ID', max_length=10)
    ups_name = forms.CharField(label='UPS name', max_length=20)
    description = forms.CharField(label='Description', max_length=200)
    count = forms.IntegerField(label='Count', validators=[MaxValueValidator(999999),MinValueValidator(1)])
    address = forms.CharField(label='Address', max_length=200)
