from django.urls import path
from . import views

urlpatterns = [ 
    path('', views.login, name='login'), 
    path('panel/', views.panel, name='panel'),
    path('logout/', views.logout, name='logout'),
]