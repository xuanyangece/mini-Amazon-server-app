from django.urls import path

from . import views

app_name = 'webserver'

urlpatterns = [
    path('homepage/', views.homepage, name='homepage'),
    path('buy/', views.buy, name='buy'),
]
