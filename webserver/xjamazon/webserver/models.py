from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User
from datetime import datetime
import uuid

class Product(models.Model):
    item_id = models.CharField(primary_key=True, max_length=20)
    description = models.CharField(max_length=200)
    rating = models.FloatField(default=0.0)
    totalscore = models.FloatField(default=0.0)
    num_of_ratings = models.IntegerField(default=0)

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
    
class AmazonUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credit = models.IntegerField(default=0)

class Package(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=30)
    order_id = models.IntegerField(default=1)
    package_id = models.IntegerField(default=1) # query
    trackingnumber = models.IntegerField(default=1)
    status = models.CharField(max_length=30, blank=True)
    product_name = models.CharField(max_length=20)
    ups_name = models.CharField(max_length=30)
    description = models.CharField(max_length=200)
    count = models.IntegerField(default=1, validators=[MaxValueValidator(999999),MinValueValidator(1)])
    x = models.IntegerField(default=1)
    y = models.IntegerField(default=1)
    date = models.DateTimeField(default=datetime.now, blank=True, editable=False)
    rating = models.FloatField(default=0.0)
    returned = models.BooleanField(default=False)

class Feedback(models.Model):
    uid = models.IntegerField(default=0)
    username = models.CharField(max_length=30)
    comment = models.CharField(max_length=200)
    reward = models.BooleanField(default=True)
