from . import views
from django.urls import path, include

urlpatterns = [
    path('google-login/', views.google_login), #로그인
    path('get-channel-id/', views.get_channel_id), #채널 아이디 가져오기 -비활성화
    path('get-youtube-list/', views.get_youtube_list), #유튜브 자기가 업로드한 영상 재생목록 id
    path('get-comment-list/', views.get_comment_list), #댓글 목록
    path('post-comment-insert/', views.post_comment_insert), #댓글 및 답글 추가
    path('get-recomment-list/', views.get_recomment_list), # 답글 리스트
    path('put-comment-update/', views.put_comment_update), # 댓글 및 답글 수정
    path('post-comment-delete/', views.post_comment_delete), #댓글 및 답글 삭제
]