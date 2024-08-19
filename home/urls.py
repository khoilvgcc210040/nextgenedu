from django.urls import include, path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('auth/', views.authPage, name='auth'),
    path('logout/', views.logoutPage, name='logout'),
    path('subjects/', views.subjects, name='subjects'),
    path('manage_classroom_detail/<int:id>/', views.manage_classroom_detail, name='manage_classroom_detail'),
    path('manage_classroom_list/', views.manage_classroom_list, name='manage_classroom_list'),
    path('create_question/<int:submission_id>/add/', views.create_question, name='create_question'),
    path('edit_question/<int:submission_id>/edit/<int:question_id>/', views.edit_question, name='edit_question'),
    path('delete_question/<int:submission_id>/delete/<int:question_id>/', views.delete_question, name='delete_question'),
    path('question_list/<int:submission_id>/', views.question_list, name='question_list'),
    path('marking/<int:assignment_id>/', views.marking, name='marking'),
    path('setting/', views.setting, name='setting'),
    path('adminPage/', views.adminPage, name='adminPage'),
    path('favorite/', views.favorite, name='favorite'),
    path('achivement/', views.achivement, name='achivement'),
    path('myclassroom/', views.myclassroom, name='myclassroom'),
    path('create_classroom/', views.create_classroom, name='create_classroom'),
    path('create_section_submission/', views.create_section_submission, name='create_section_submission'),
    path('subsection/<int:subsection_id>/upload/', views.upload_subsection_file, name='upload_subsection_file'),
    path('classroom/<int:classroom_id>/section/<int:section_id>/update/', views.update_section, name='update_section'),
    path('classroom/<int:classroom_id>/update/', views.update_classroom_description, name='update_classroom_description'),
    path('classroom/<int:classroom_id>/submission/<int:submission_id>/update/', views.update_submission, name='update_submission'),
    path('subjects/<int:subject_id>/grade/<int:grade>/classrooms/', views.classrooms, name='classrooms'),
    path('classroom/<int:id>/', views.classroom_detail, name='classroom_detail'),
    path('setting_classroom/<int:id>/', views.setting_classroom, name='setting_classroom'),
    path('enter-password/<int:classroom_id>/', views.enter_password, name='enter_password'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
