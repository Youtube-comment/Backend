from . import views
from django.urls import path, include

urlpatterns = [
    path('google-login/', views.google_login),
    path('get-youtube-list/', views.get_youtube_list),
]