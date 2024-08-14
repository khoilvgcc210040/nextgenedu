from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('auth/', views.authPage, name='auth'),
    path('logout/', views.logoutPage, name='logout'),
    path('subjects/', views.subjects, name='subjects'),
    path('manage_classroom/', views.manage_classroom, name='manage_classroom'),
    path('create_question/', views.create_question, name='create_question'),
    path('question_list/', views.question_list, name='question_list'),
    path('marking/', views.marking, name='marking'),
    path('setting/', views.setting, name='setting'),
    path('adminPage/', views.adminPage, name='adminPage'),
    path('favorite/', views.favorite, name='favorite'),
    path('achivement/', views.achivement, name='achivement'),
    path('subjects/<int:subject_id>/grade/<int:grade>/classrooms/', views.classrooms, name='classrooms'),
    path('classroom/<int:id>/', views.classroom_detail, name='classroom_detail'),
    path('setting_classroom/<int:id>/', views.setting_classroom, name='setting_classroom'),
    path('enter-password/<int:classroom_id>/', views.enter_password, name='enter_password'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
]
