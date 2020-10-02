from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from .models import *
# Register your models here.


class PaymentsInline(admin.StackedInline):
    model = Payment
    extra = 0
    classes = ['collapse']


class RentalInline(admin.StackedInline):
    model = Rental
    extra = 0
    classes = ['collapse']


class PurchaseInLine(admin.StackedInline):
    model = ItemPurchase
    extra = 0
    classes = ['collapse']


class DGUserAdmin(BaseUserAdmin):
    inlines = [PaymentsInline, RentalInline, PurchaseInLine]

    fieldsets = [
        (None, {'fields': ['username', 'membership']}),
        ('Personal Info', {'fields': ['first_name', 'last_name', 'email']}),
        ('Important dates', {'fields': ['last_login', 'date_joined']}),
        ('Permissions', {'fields': ['is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'],
                         'classes': ['collapse']}) 
    ]

    list_display = ['username', 'get_full_name', 'email', 'account_balance', 'membership']


class EquipmentPriceInLine(admin.TabularInline):
    model = EquipmentPrice
    extra = 0


class EquipmentCategoryAdmin(admin.ModelAdmin):
    model = EquipmentCategory

    class Meta:
        verbose_name = 'Equipment Category'
        verbose_name_plural = 'Equipment Categories'


class EquipmentAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['category', 'label', 'description']})
    ]
    inlines = [EquipmentPriceInLine]

    class Meta:
        verbose_name = 'Equipment'
        verbose_name_plural = 'Equipment'


class ItemPriceInline(admin.TabularInline):
    model = ItemPrice
    extra = 0
    fieldsets = [
        (None, {'fields': ['membership', 'price']})
    ]


class ItemAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['label', 'rental_related', 'price_per_unit']})
    ]
    inlines = [ItemPriceInline]


admin.site.register(User, DGUserAdmin)
admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(EquipmentCategory, EquipmentCategoryAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Membership)
admin.site.register(Reservation)
admin.site.register(Rental)
