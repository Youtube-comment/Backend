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
from rest_framework_simplejwt.tokens import RefreshToken
import jwt
from django.http import JsonResponse

@csrf_exempt
def get_channel_id(request):
    token = request
    response = requests.get('https://www.googleapis.com/youtube/v3/channels', params={
          'access_token': token,
          'part': 'snippet',
          'key': 'AIzaSyAVU2_JX41C1c4k3i9V2N5yDEf2_cldpLw',
          'mine': True,     
     })
    
    channel_id = response.json()
    return channel_id.get('items')[0]['id']

@csrf_exempt
def get_channel_sb(request):
    token = request
    response = requests.get('https://www.googleapis.com/youtube/v3/channels', params={
          'access_token': token,
          'part': 'snippet',
          'key': 'AIzaSyAVU2_JX41C1c4k3i9V2N5yDEf2_cldpLw',
          'mine': True,
     })
    
    subscriber = response.json()
    return JsonResponse({'data' : subscriber})

@csrf_exempt
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['g_id'] = user.g_id
    refresh['mail'] = user.mail

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

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
            jwt = get_tokens_for_user(user)
            channel_id = get_channel_id(access_token)
            user.channel_id = channel_id
            user.save()
            print(channel_id)
            return JsonResponse({'email': email_req_json, 'new' : "기존회원",  "jwt" : jwt, "access" : channel_id})
        except User.DoesNotExist:
            new_user = User(name=email_req_json.get('name'), mail=email, g_id=email_req_json.get('id'), access_token=access_token, channel_id = "")
            new_user.save()
            channel_id = get_channel_id(access_token)
            new_user.channel_id = channel_id
            new_user.save()
            jwt = get_tokens_for_user(user)
            return JsonResponse({'email': email_req_json, 'new' : "신입회원", "jwt" : jwt})

        


@csrf_exempt
def get_youtube_list(request):
    # Get the access token
    token = request.META.get('HTTP_AUTHORIZATION', None)
    if not token:
        return JsonResponse({'error': 'No token provided'}, status=401)

    # Decode the token and retrieve the user ID and email from the payload
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload['g_id']
    except jwt.ExpiredSignatureError:
        return JsonResponse({'error': 'Token expired'}, status=401) 
    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Invalid token'}, status=401)

    # Retrieve the user object based on the user ID
    try:
        user = User.objects.get(g_id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=401)

    # Send a request to the YouTube API to retrieve the list of videos uploaded by the user
    response = requests.get('https://www.googleapis.com/youtube/v3/channels', params={
        'part': 'contentDetails',
        'id': user.channel_id,
        'access_token': user.access_token,
    })

    # Process the response from the YouTube 
    try:
        youtube_list = response.json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        response2 = requests.get('https://www.googleapis.com/youtube/v3/playlistItems', params={
        'part': 'snippet',
        'playlistId': youtube_list,
        'access_token': user.access_token,
    })
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=401)
    return JsonResponse(response2.json())

@csrf_exempt
def get_comment_list(request):
    # 액세스 토큰 가져오기
    data = json.loads(request.body.decode('utf-8'))
    comment_id = data.get('id')
    token = request.META.get('HTTP_AUTHORIZATION', None)
    if not token:
        return JsonResponse({'error': 'No token provided'}, status=401)

    # Decode the token and retrieve the user ID from the payload
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload['g_id']
        user_mail = payload['mail']
    except jwt.ExpiredSignatureError:
        return JsonResponse({'error': 'Token expired'}, status=401) 
    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Invalid token'}, status=401)

    # Retrieve the user object based on the user ID
    try:
        user = User.objects.get(g_id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=401)

    # 유튜브 API 요청 보내기
    response = requests.get('https://www.googleapis.com/youtube/v3/commentThreads', params={
        'part': 'snippet',
        'videoId' : comment_id,  #프론트에서 다시 videoId 돌려 받아야함
        'textFormat': 'plainText',
        'access_token': user.access_token,
    })

    # 유튜브 API 응답 처리
    comment_list = response.json()
    return JsonResponse(comment_list)

@csrf_exempt
def get_recomment_list(request):
    # 액세스 토큰 가져오기
    token = request.META.get('HTTP_AUTHORIZATION', None)
    # parentid 가져오기
    data = json.loads(request.body.decode('utf-8'))
    parentId = data.get('parentId')
    if not token:
        return JsonResponse({'error': 'No token provided'}, status=401)

    # Decode the token and retrieve the user ID from the payload
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload['g_id']
    except jwt.ExpiredSignatureError:
        return JsonResponse({'error': 'Token expired'}, status=401) 
    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Invalid token'}, status=401)

    # Retrieve the user object based on the user ID
    try:
        user = User.objects.get(g_id=user_id)
        print(user.access_token)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=401)

    # 유튜브 API 요청 보내기
    response = requests.get('https://www.googleapis.com/youtube/v3/comments', params={
        'part': 'snippet',
        "parentId": parentId, 
        'access_token': user.access_token,
    })

    # 유튜브 API 응답 처리
    comment_list = response.json()
    return JsonResponse(comment_list)

@csrf_exempt
def post_comment_insert(request):
    # 액세스 토큰 가져오기
    token = request.META.get('HTTP_AUTHORIZATION', None)
    # parentid 가져오기
    data = json.loads(request.body.decode('utf-8'))
    parentId = data.get('parentId')
    # parentid 가져오기
    textOriginal = data.get('textOriginal')
    if not token:
        return JsonResponse({'error': 'No token provided'}, status=401)

    # Decode the token and retrieve the user ID from the payload
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload['g_id']
    except jwt.ExpiredSignatureError:
        return JsonResponse({'error': 'Token expired'}, status=401) 
    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Invalid token'}, status=401)

    # Retrieve the user object based on the user ID
    try:
        user = User.objects.get(g_id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=401)

    # 유튜브 API 요청 보내기
    payload = {
    'snippet': {
        'parentId': parentId,
        'textOriginal': textOriginal,
        }
    }

    response = requests.post('https://www.googleapis.com/youtube/v3/comments', params={
        'part': 'snippet',
        'access_token': user.access_token,
    },
    json=payload
    )

    # 유튜브 API 응답 처리
    comment_list = response.json()
    return JsonResponse(comment_list)

@csrf_exempt
def put_comment_update(request):
    # 액세스 토큰 가져오기
    token = request.META.get('HTTP_AUTHORIZATION', None)
    #id 가져오기
    data = json.loads(request.body.decode('utf-8'))
    Id = data.get('id')
    textOriginal = data.get('textOriginal')

    if not token:
        return JsonResponse({'error': 'No token provided'}, status=401)

    # Decode the token and retrieve the user ID from the payload
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload['g_id']
    except jwt.ExpiredSignatureError:
        return JsonResponse({'error': 'Token expired'}, status=401) 
    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Invalid token'}, status=401)

    # Retrieve the user object based on the user ID
    try:
        user = User.objects.get(g_id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=401)
    # 유튜브 API 요청 보내기
    payload = {
    'snippet': {
        'id': Id,
        'textOriginal': textOriginal,
        }
    }

    response = requests.put('https://www.googleapis.com/youtube/v3/comments', params={
        'part': 'snippet',
        'access_token': user.access_token,
    },
    json=payload
    )
    comment_list = response.json()
    return JsonResponse(comment_list)

@csrf_exempt
def post_comment_delete(request):
    # 액세스 토큰 가져오기
    token = request.META.get('HTTP_AUTHORIZATION', None)
    # parentid 가져오기
    data = json.loads(request.body.decode('utf-8'))
    comment_id = data.get('comment_id')

    if not token:
        return JsonResponse({'error': 'No token provided'}, status=401)

    # Decode the token and retrieve the user ID from the payload
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload['g_id']
    except jwt.ExpiredSignatureError:
        return JsonResponse({'error': 'Token expired'}, status=401) 
    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Invalid token'}, status=401)

    # Retrieve the user object based on the user ID
    try:
        user = User.objects.get(g_id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=401)


    response = requests.delete('https://www.googleapis.com/youtube/v3/comments', params={
        'id' : comment_id,
        'access_token': user.access_token,
        }
    )

    # 유튜브 API 응답 처리
    comment_list = response.json()
    return JsonResponse(comment_list)