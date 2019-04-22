from django.contrib import admin
from .models import BuyProduct, Warehouse, AmazonUser, Package

# Register your models here.
admin.site.register(AmazonUser)
admin.site.register(BuyProduct)
admin.site.register(Warehouse)
admin.site.register(Package)
