from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from dgsys2.models import *


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'membership', 'membership_label', 'account_balance', 'password')

    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['amount', 'user', 'date', 'explanation']


class EquipmentPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentPrice
        fields = ['price', 'membership']


class RentalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rental
        fields = '__all__'


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'


class ExpandedReservationSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    class Meta:
        model = Reservation
        fields = '__all__'
        depth = 1


class EquipmentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentCategory
        fields = ['label']


class EquipmentSerializer(serializers.ModelSerializer):
    many = True
    category = serializers.StringRelatedField()

    class Meta:
        model = Equipment
        fields = ['id', 'category', 'label', 'description']


class RentalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rental
        fields = '__all__'


class RentalSerializerNoArticles(serializers.ModelSerializer):

    class Meta:
        model = Rental
        fields = ['id', 'start_date', 'estimated_end', 'end_date', 'amount']
