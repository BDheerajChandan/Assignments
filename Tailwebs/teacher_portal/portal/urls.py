from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('home/', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('update/', views.update_student, name='update_student'),
    path('delete/', views.delete_student, name='delete_student'),
    path('add/', views.add_student, name='add_student'),
]
