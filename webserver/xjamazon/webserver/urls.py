from django.urls import path

from . import views

app_name = 'webserver'

urlpatterns = [
    path('homepage/', views.homepage, name='homepage'),
    path('close/', views.close, name='close'),
    path('createWarehouse/', views.createWarehouse, name='createWarehouse'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('buyProduct/<int:id>', views.buyProduct, name='buyProduct'),
    path('dashboard/<int:id>/', views.dashboard, name='dashboard'),
    path('query/<int:id>/', views.query, name='query'),
    path('query/<int:id>/package/<int:pid>/', views.querypackage, name='querypackage'),
    path('logout/', views.logout, name='logout'),
]
