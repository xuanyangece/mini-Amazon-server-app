from django.urls import path

from . import views

app_name = 'webserver'

urlpatterns = [
    path('homepage/', views.homepage, name='homepage'),
    path('buyProduct/', views.buyProduct, name='buyProduct'),
    path('createWarehouse/', views.createWarehouse, name='createWarehouse'),
]
