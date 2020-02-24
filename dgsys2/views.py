from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import Group
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from dgsys2.models import User
from dgsys2.serializers import UserSerializer, GroupSerializer


@api_view(['GET', 'POST'])
@csrf_exempt
def users(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)

    elif request.method == 'GET':
        if request.user.is_authenticated:
            serializer = UserSerializer(request.user)
            return JsonResponse(serializer.data, status=200)
        else:
            data = {'error': 'Not logged in'}
            return JsonResponse(data, status=304)
