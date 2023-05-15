from . import views
from django.urls import path, include

urlpatterns = [
    path('google-login/', views.google_login),
    path('get-channel-id/', views.get_channel_id),
    path('get-youtube-list/', views.get_youtube_list),
    path('get-comment-list/', views.get_comment_list),
    path('post-comment-insert/', views.post_comment_insert),
]