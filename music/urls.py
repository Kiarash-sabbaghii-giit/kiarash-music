from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('play/<int:song_id>/', views.play_song, name='play_song'),
    path('stream/<int:song_id>/', views.stream_audio, name='stream_audio'),
    path('search/', views.search_suggestions, name='search_suggestions'),
    path('about/', views.about, name='about'),
    path('register/', views.register_view, name='register'),

    # استفاده مستقیم از ویوهای احراز هویت جنگو
    path('login/', auth_views.LoginView.as_view(template_name='music/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
]