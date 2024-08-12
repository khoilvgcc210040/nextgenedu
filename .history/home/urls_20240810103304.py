from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('auth/', views.authPage, name='auth'),
    path('', views.home, name='home'),
]
