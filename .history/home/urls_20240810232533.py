from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('auth/', views.authPage, name='auth'),
    path('logout/', views.logoutPage, name='logout'),
    path('subjects/', views.subjects, name='subjects'),
    path('clerk-login/', views.clerk_login, name='clerk_login'),
]
