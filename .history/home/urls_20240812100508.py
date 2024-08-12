from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('auth/', views.authPage, name='auth'),
    path('logout/', views.logoutPage, name='logout'),
    path('subjects/', views.subjects, name='subjects'),
    path('subjects/<int:subject_id>/grade/<int:grade>/classrooms/', views.classrooms, name='classrooms'),
    path('classroom/<int:id>/', views.classroom_detail, name='classroom_detail'),
     path('enter-password/<int:classroom_id>/', views.enter_password, name='enter_password'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
]
