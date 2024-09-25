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
    path('classroom/submission/<int:file_id>/update/', views.update_file_submission, name='update_file_submission'),
    path('classroom/submission/<int:file_id>/delete/', views.delete_file_submission, name='delete_file_submission'),
    path('update_classroom/<int:classroom_id>/', views.update_classroom, name='update_classroom'),
    path('delete_classroom/<int:classroom_id>/', views.delete_classroom, name='delete_classroom'),
    path('subjects/<int:subject_id>/grade/<int:grade>/classrooms/', views.classrooms, name='classrooms'),
    path('classroom/<int:id>/', views.classroom_detail, name='classroom_detail'),
    path('setting_classroom/<int:id>/', views.setting_classroom, name='setting_classroom'),
    path('enter-password/<int:classroom_id>/', views.enter_password, name='enter_password'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    path('submission/<int:submission_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('submission/<int:submission_id>/question/<int:question_id>/', views.take_quiz, name='take_quiz'),
    path('exit_quiz/<int:submission_id>/', views.exit_quiz, name='exit_quiz'),
    path('submission/<int:submission_id>/question/<int:question_id>/submit/', views.submit_answer, name='submit_answer'),
    path('submission/<int:submission_id>/result/', views.quiz_result, name='quiz_result'),
    path('save_message/', views.save_message, name='save_message'),
    path('favorite_classroom/<int:classroom_id>/', views.favorite_classroom, name='favorite_classroom'),
    path('update-notification-preference/', views.update_notification_preference, name='update_notification_preference'),
    path('update_allow_chat/<int:classroom_id>/', views.update_allow_chat, name='update_allow_chat'),
    path('delete_section/<int:section_id>/', views.delete_section, name='delete_section'),
    path('delete_submission/<int:submission_id>/', views.delete_submission, name='delete_submission'),
    path('delete_member/', views.delete_member, name='delete_member'),
    path('block_member/', views.block_member, name='block_member'),
    path('classroom/<int:classroom_id>/unblock/', views.unblock_participant, name='unblock_participant'),
    path('classroom/<int:classroom_id>/join/', views.join_classroom, name='join_classroom'),
    path('search/', views.searchPage, name='searchPage'),
    path('question_test_marking/<int:submission_id>/', views.question_test_marking, name='question_test_marking'),
    path('view_answer_history/<int:quiz_result_id>/', views.view_answer_history, name='view_answer_history'),
    path('edit_submission_time/', views.edit_submission_time, name='edit_submission_time'),
    path('update-account/', views.update_account, name='update_account'),
    path('auth-receiver/', views.auth_receiver, name='auth_receiver'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),

    path('forum/<int:classroom_id>/', views.forum, name='forum'),
    path('forum/<int:post_id>/detail/', views.forum_detail, name='forum_detail'),
    path('forum/<int:classroom_id>/create/', views.create_post, name='create_post'),
    path('forum/<int:classroom_id>/manage/', views.manage_posts, name='manage_posts'),
    path('forum/post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('forum/post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('forum/<int:classroom_id>/manage_approve/', views.manage_approve_posts, name='manage_approve_posts'),
    path('forum/post/<int:post_id>/approve/', views.approve_post, name='approve_post'),
    path('forum/post/<int:post_id>/reject/', views.reject_post, name='reject_post'),
    path('forum/post/<int:post_id>/comment/', views.add_comment, name='add_comment'),

    path('classify/', views.classify, name='classify'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('notification/', views.notification, name='notification'),
    path('join/<str:link>/', views.access_join_classroom, name='access_join_classroom'),
    path('leave_classroom/<int:classroom_id>/', views.leave_classroom, name='leave_classroom'),
    path('edit_assignment_time/', views.edit_assignment_time, name='edit_assignment_time'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
