from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('auth/', views.authPage, name='auth'),
    path('logout/', views.logoutPage, name='logout'),
    path('subjects/', views.subjects, name='subjects'),
    path('subjects/', views.subjects, name='subjects'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
]
