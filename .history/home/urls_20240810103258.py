from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('', views.auth, name='auth'),
    path('', views.home, name='home'),
]
