from datetime import datetime

from django.db.models import Subquery, Prefetch
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import Group
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, filters
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework_simplejwt.views import TokenObtainPairView

from dgsys2.models import *
from dgsys2.serializers import *

import datetime
import dateutil.parser

from dgsys2.view_utils import *


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


@api_view(['GET', 'POST'])
@csrf_exempt
def payment(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        data['user'] = request.user.id
        serializer = PaymentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        else:
            return JsonResponse(serializer.errors, status=400)





@api_view(['GET'])
@csrf_exempt
def equipment(request):
    equipment_items = Equipment.objects.all()
    equipment_list = []

    if None not in (request.GET.get('from', None), request.GET.get('to', None)):
        from_date = dateutil.parser.parse(request.GET['from'])
        to_date = dateutil.parser.parse(request.GET['to'])
        for item in equipment_items:
            equipment_list.append(serializeEquipment(item, request, from_date, to_date))
    else:
        for item in equipment_items:
            equipment_list.append(serializeEquipment(item, request))

    data = {'data': equipment_list}
    return JsonResponse(data, status=200)


@api_view(['GET'])
@csrf_exempt
def equipment_category(request):
    categories = EquipmentCategory.objects.all()
    serializer = EquipmentCategorySerializer(categories, many=True)
    return JsonResponse({'data': serializer.data})


@api_view(['GET', 'POST'])
@csrf_exempt
def reservation(request):
    # GET: Get all for the logged in user
    # POST: New booking
    # PUT: Update existing booking
    if request.method == 'GET':
        if request.user.is_authenticated:
            bookings = Reservation.objects.filter(
                user=request.user
            )
            serializer = ExpandedReservationSerializer(bookings, many=True)
            data = {'data': serializer.data}
            return JsonResponse(data)
        else:
            return JsonResponse({'error': 'User is not logged in'})

    if request.method == 'POST':
        if request.user.is_authenticated:
            data = JSONParser().parse(request)
            data['user'] = request.user.id
            serializer = ReservationSerializer(data=data)
            if serializer.is_valid():
                if equipment_is_available(data['equipment_articles'], data['start_date'], data['end_date']):
                    serializer.save()
                    return JsonResponse(serializer.data, status=201)
                else:
                    return occupied_response()
            else:
                return JsonResponse(serializer.errors, status=400)
        else:
            return JsonResponse({'error': 'User is not logged in'})




@api_view(['GET', 'POST'])
@csrf_exempt
def rental(request):
    if request.method == 'GET' and request.user.is_authenticated:
        rentals = Rental.objects.filter(
            user=request.user
        )
        serializer = RentalSerializer(rentals, many=True)
        data = {'data': serializer.data}
        return JsonResponse(data)

    if request.method == 'POST' and request.user.is_authenticated:
        data = JSONParser().parse(request)
        data['user'] = request.user.id
        serializer = RentalSerializer(data=data)
        if serializer.is_valid():
            if equipment_is_available(
                    data['equipment_articles'],
                    data['start_date'],
                    data['estimated_end'],
                    False):
                serializer.save()
                return JsonResponse(data, status=201)
            return occupied_response()


@api_view(['GET', 'PUT'])
@csrf_exempt
def rental_detail(request, pk):
    try:
        rental = Rental.objects.filter(user=request.user).get(pk=pk)
    except Rental.DoesNotExist:
        return Response(status=404)

    if request.method == 'GET':
        serializer = RentalSerializer(rental)
        return JsonResponse({'data': serializer.data})

    if request.method == 'PUT':
        data = JSONParser().parse(request)
        if data['end_date'] is not None:
            triggered_upgrade = upgrade_if_eligible(request.user)
            end_date = dateutil.parser.parse(data['end_date'])
            rental.end_date = end_date
            rental.amount = total_rental_price(
                request.user,
                rental.equipment_articles.all(),
                rental.start_date,
                rental.end_date
            )
            rental.save()
            serialized_rental = RentalSerializerNoArticles(rental).data
            serialized_rental['equipment_articles'] =\
                [serializeEquipment(item, request) for item in rental.equipment_articles.all()]
            data = {
                'meta:': {
                    'triggered_upgrade': triggered_upgrade
                },
                'data': serialized_rental
            }
            return JsonResponse(data)
        else:
            return JsonResponse({'error': 'PUT can only update field end_date'}, status=400)


@api_view(['GET'])
@csrf_exempt
def rental_open(request):
    if request.method == 'GET' and request.user.is_authenticated:
        rentals = Rental.objects.filter(
            user=request.user,
            end_date__isnull=True
        )
        serialized_rentals = []
        for rental in rentals:
            serialized = RentalSerializerNoArticles(rental).data
            serialized['equipment_articles'] = [serializeEquipment(item, request) for item in rental.equipment_articles.all()]
            serialized_rentals.append(serialized)

        data = {'data': serialized_rentals}
        return JsonResponse(data)
