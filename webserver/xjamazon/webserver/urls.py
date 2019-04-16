from django.urls import path

from . import views

app_name = 'webserver'

urlpatterns = [
    path('homepage/', views.homepage, name='homepage'),
    path('getProduct/', views.getProduct, name='getProduct'),
    path('buyProduct/', views.buyProduct, name='buyProduct'),
    path('createWarehouse/', views.createWarehouse, name='createWarehouse'),
]
