from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

class Product(models.Model):
    item_id = models.CharField(max_length=20)
    description = models.CharField(max_length=200)
    count = models.IntegerField(default=1, validators=[MaxValueValidator(999999),MinValueValidator(1)])

class BuyProduct(models.Model):
    item_id = models.CharField(max_length=20)
    ups_name = models.CharField(max_length=30)
    description = models.CharField(max_length=200)
    count = models.IntegerField(default=1, validators=[MaxValueValidator(999999),MinValueValidator(1)])
    x = models.IntegerField(default=1)
    y = models.IntegerField(default=1)

class Warehouse(models.Model):
    whID = models.CharField(max_length=20)
    x = models.IntegerField(default=1)
    y = models.IntegerField(default=1)
    
