from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.home, name='home'),
    path('distance/', views.distance, name='distance'),
    path('get_distance/', views.get_distance, name='get_distance'),
    path('subjects/', views.subjects, name='subjects'),
    path('list_courses/<str:pk>/', views.list_courses, name='list_courses'),
    path('textSum/', views.textSum, name='textSum'),
    path('pdfSum/', views.pdfSum, name='pdfSum'),
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutPage, name='logout'),
    path('register/', views.registerPage, name='register'),
    path('upload/', views.uploadPage, name='upload'),
    path('socialList/', views.social_content_list, name='socialList'),
    path('socialDetail/<int:pk>/', views.social_content_detail, name='social_content_detail'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
