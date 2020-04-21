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
from dgsys2.serializers import UserSerializer, PaymentSerializer, EquipmentSerializer, ReservationSerializer, \
    ExpandedReservationSerializer, EquipmentCategorySerializer

import datetime
import dateutil.parser


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


def serializeEquipment(item, request, from_date=None, to_date=None):
    price = EquipmentPrice.objects.filter(
        equipment_article__id=item.id,
        membership=request.user.membership
    ).values('price')[0]['price']

    occupants = ""

    if from_date is not None and to_date is not None:
        print()
        rentals = Rental.objects.filter(
            equipment_articles=item,
            start_date__range=(from_date, to_date),
            end_date__range=(from_date, to_date),
        ).values("user__first_name", "user__last_name").distinct()

        reservations = Reservation.objects.filter(
            equipment_articles__label=item,
            start_date__range=(from_date, to_date),
            end_date__range=(from_date, to_date),
        ).values("user__first_name", "user__last_name").distinct()

        for r in rentals:
            if len(occupants) > 0:
                occupants += ", "
            occupants += r['user__first_name'] + " " + r['user__last_name'][0]

        for r in reservations:
            if len(occupants) > 0:
                occupants += ", "
            occupants += r['user__first_name'] + " " + r['user__last_name'][0]

    item_dict = {
        'category': item.category.label,
        'category_id': item.category_id,
        'id': item.id,
        'description': item.description,
        'label': item.label,
        'price': price,
        'occupants': occupants
    }

    return item_dict


@api_view(['GET'])
@csrf_exempt
def equipment(request):

    if None not in (request.GET.get('from', None), request.GET.get('to', None)):

        from_date = dateutil.parser.parse(request.GET['from'])
        to_date = dateutil.parser.parse(request.GET['to'])


        available_eq = Equipment.objects.exclude(
            rental__start_date__range=(from_date, to_date),
            rental__end_date__range=(from_date, to_date),
        ).exclude(
            reservation__start_date__range=(from_date, to_date),
            reservation__end_date__range=(from_date, to_date),
        )

        occupied_eq = Equipment.objects.exclude(
            id__in=available_eq
        )

        serialized_available = []
        serialized_unavailable = []

        for item in available_eq:
            serialized_available.append(serializeEquipment(item, request))

        for item in occupied_eq:
            serialized_unavailable.append(serializeEquipment(item, request, from_date, to_date))

        data = {
            'data': {
                'available': serialized_available,
                'occupied': serialized_unavailable
            }
        }

        return JsonResponse(data, status=200)
    else:
        equipment_items = Equipment.objects.all()
        equipment_list = []
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
                    return JsonResponse({'error': 'Selected equipment is occupied'}, status=412)
            else:
                return JsonResponse(serializer.errors, status=400)
        else:
            return JsonResponse({'error': 'User is not logged in'})


def equipment_is_available(equipmentIds, from_date, to_date):
    available = True

    for eq_id in equipmentIds:
        rentals = Rental.objects.filter(
            equipment_articles__id=eq_id,
            start_date__range=(from_date, to_date),
            end_date__range=(from_date, to_date),
        ).count()

        reservations = Reservation.objects.filter(
            equipment_articles__id=eq_id,
            start_date__range=(from_date, to_date),
            end_date__range=(from_date, to_date),
        ).count()

        if rentals > 0 or reservations > 0:
            available = False

    return available
