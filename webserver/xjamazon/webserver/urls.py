from django.urls import path

from . import views

app_name = 'webserver'

urlpatterns = [
    path('homepage/', views.homepage, name='homepage'),
    path('feedback/view/', views.viewfb, name='viewfb'),
    path('feedback/reward/<int:id>', views.rewardfb, name='rewardfb'),
    path('close/', views.close, name='close'),
    path('createWarehouse/', views.createWarehouse, name='createWarehouse'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('feedback/offer/<int:id>/', views.offerfb, name='offerfb'),
    path('buyProduct/<int:id>/', views.buyProduct, name='buyProduct'),
    path('searchProduct/<int:id>/', views.searchProduct, name='searchProduct'),
    path('returnProduct/<int:id>/<int:pid>/', views.returnProduct, name='returnProduct'),
    path('dashboard/<int:id>/', views.dashboard, name='dashboard'),
    path('query/<int:id>/', views.query, name='query'),
    path('query/<int:id>/package/<int:pid>/', views.querypackage, name='querypackage'),
    path('logout/', views.logout, name='logout'),
]
