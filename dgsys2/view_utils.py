from django.db.models import Q
from django.http import JsonResponse

from dgsys2.models import *
from datetime import date, datetime


def occupied_response():
    return JsonResponse({'error': 'Selected equipment is occupied'}, status=412)


def equipment_is_available(equipmentIds, from_date, to_date, include_reservations=True):
    available = True

    for eq_id in equipmentIds:
        rentals = Rental.objects.filter(
            equipment_articles__id=eq_id,
            start_date__lt=to_date,
            end_date__gt=from_date
        ).count()

        if rentals > 0:
            available = False

        if include_reservations and available:
            reservations = Reservation.objects.filter(
                equipment_articles__id=eq_id,
                start_date__lt=to_date,
                end_date__gt=from_date
            ).count()

            if reservations > 0:
                available = False

    return available


def serializeEquipment(item, request, from_date=None, to_date=None):
    price = EquipmentPrice.objects.filter(
        equipment_article__id=item.id,
        membership=request.user.membership
    ).values('price')[0]['price']

    occupants = ""

    is_rented = False
    is_reserved = False

    if from_date is not None and to_date is not None:
        print()
        rentees = Rental.objects.filter(
            Q(end_date__gt=from_date) | Q(end_date__isnull=True),
            equipment_articles__label=item.label,
            start_date__lt=to_date
        ).values("user__first_name", "user__last_name").distinct()
        is_rented = rentees.count() > 0

        reservators = Reservation.objects.filter(
            equipment_articles__label=item,
            start_date__lt=to_date,
            end_date__gt=from_date
        ).values("user__first_name", "user__last_name").distinct()
        is_reserved = reservators.count() > 0

        occupants_qs = reservators.union(rentees).distinct()

        for o in occupants_qs:
            if len(occupants) > 0:
                occupants += ", "
            occupants += o['user__first_name'] + " " + o['user__last_name'][0]

    item_dict = {
        'category': item.category.label,
        'category_id': item.category_id,
        'id': item.id,
        'description': item.description,
        'label': item.label,
        'price': price,
        'occupants': occupants,
        'is_reserved': is_reserved,
        'is_rented': is_rented
    }

    return item_dict


def total_rental_price(user, items, start_date, end_date):
    start_date = start_date.replace(tzinfo=None)
    end_date = end_date.replace(tzinfo=None)

    date_difference = end_date - start_date

    if date_difference.days > 2 and user.membership.id == 2:
        membership = Membership.objects.get(pk=3)
    else:
        membership = user.membership

    days_rented = date_difference.days + 1

    total_price = 0

    for item in items:
        item_price = EquipmentPrice.objects.get(
            equipment_article=item,
            membership=membership
        ).price

        total_price += item_price * days_rented

    return total_price


def upgrade_if_eligible(user):
    if user.is_member():
        intervals = select_semester(date.today())
        end_date = intervals['end']
        start_date = intervals['start']
        rentals_this_semester = Rental.objects.filter(
            user=user,
            end_date__gte=start_date,
            end_date__lte=end_date,
        ).count()

        if rentals_this_semester >= 5:
            user.membership = Membership.objects.get(pk=3)
            user.save()
            return True
    return False


def select_semester(check_date: date):
    current_year = date.today().year
    if date(current_year, 9, 1) >= check_date >= date(current_year, 12, 31):
        return {'start': datetime(current_year, 9, 1), 'end': datetime(current_year, 12, 31)}
    else:
        return {'start': datetime(current_year, 1, 1), 'end': datetime(current_year, 8, 31)}


def reset_plus_memberships():
    plus_members = User.objects.get(membership=3).all()
    for member in plus_members:
        member.membership = Membership.objects.get(pk=2).first()
        member.save()


def serialized_items(user):
    membership = user.membership
    itemset = Item.objects.all()
    result = []
    for item in itemset:
        try:
            price = ItemPrice.objects.get(
                item=item,
                membership=membership
            )
            print(price)
            result.append({
                'id': item.id,
                'label': item.label,
                'price': price.price,
                'rental_related': item.rental_related,
                'price_per_unit': item.price_per_unit
            })
        except ItemPrice.DoesNotExist:
            result.append({
                'id': item.id,
                'label': item.label,
                'price': 0,
                'rental_related': item.rental_related,
                'price_per_unit': item.price_per_unit
            })

    return result
