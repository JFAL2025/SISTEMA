from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('panel/', views.panel, name='panel'),           # Menú principal
   path('admin.html/', views.admin_panel, name='admin.html'),
           path('logout/', views.logout, name='logout'),
]