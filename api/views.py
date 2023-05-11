from django.shortcuts import render
from django.http import JsonResponse
from google.oauth2 import id_token
import json
import requests
from django.views.decorators.csrf import csrf_exempt
from json import JSONDecodeError
import requests
import os
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.models import User
@csrf_exempt
def google_login(request):
        data = json.loads(request.body)
        code = data.get('code')
        client_id = settings.GOOGLE_CLIENT_ID
        client_secret = settings.GOOGLE_CLIENT_SECRET
        GOOGLE_CALLBACK_URI = "http://localhost:3000"

        token_req = requests.post(f"https://oauth2.googleapis.com/token?client_id={client_id}&client_secret={client_secret}&code={code}&grant_type=authorization_code&redirect_uri={GOOGLE_CALLBACK_URI}")
        
        token_req_json = token_req.json()
        error = token_req_json.get("error")

        if error is not None:
            return JsonResponse({'err_msg': error, 'token' : code})

        access_token = token_req_json.get('access_token')
        print(access_token)

        email_req = requests.get(f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}")
        email_req_status = email_req.status_code

        if email_req_status != 200:
            return JsonResponse({'err_msg': 'failed to get email'})

        email_req_json = email_req.json()
        email = email_req_json.get('email')
        try:
            user = User.objects.get(mail=email)
            user.access_token = access_token
            user.save()
            return JsonResponse({'email': email_req_json, 'new' : "기존회원", 'token': access_token})
        except User.DoesNotExist:
            new_user = User(name=email_req_json.get('name'), mail=email, g_id=email_req_json.get('id'), access_token=access_token)
            new_user.save()
            return JsonResponse({'email': email_req_json, 'new' : "신입회원"})

@csrf_exempt
def get_youtube_list(request):
    # 액세스 토큰 가져오기
    access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]

    # 유튜브 API 요청 보내기
    response = requests.get('https://www.googleapis.com/youtube/v3/search', params={
        'part': 'snippet',
        'channelId' : 'UCfkB07bG6AWCS2NSz8BZCkw',
        'access_token': access_token,
    })

    # 유튜브 API 응답 처리
    youtube_list = response.json()
    return JsonResponse(youtube_list)