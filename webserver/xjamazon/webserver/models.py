from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

class Item(models.Model):
    item_id = models.CharField(max_length=10)
    ups_name = models.CharField(max_length=20)
    description = models.CharField(max_length=200)
    count = models.IntegerField(default=1, validators=[MaxValueValidator(999999),MinValueValidator(1)])
    address = models.CharField(max_length=200)
