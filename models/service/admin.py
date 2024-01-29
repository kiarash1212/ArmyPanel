from django.contrib import admin
from jalali_date import datetime2jalali
from jalali_date.admin import ModelAdminJalaliMixin

from models.service.models import Country, Period, Service


@admin.register(Country)
class CountryAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = [
        'name',
        'is_active',
        'get_created_jalali'
    ]
    search_fields = ['name']

    @admin.display(description='تاریخ ایجاد', ordering='created')
    def get_created_jalali(self, obj):
        return datetime2jalali(obj.published)


@admin.register(Period)
class PeriodAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = [
        'name',
        'is_active',
        'get_created_jalali'
    ]

    @admin.display(description='تاریخ ایجاد', ordering='created')
    def get_created_jalali(self, obj):
        return datetime2jalali(obj.published)


@admin.register(Service)
class ServiceAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = [
        'id',
        'country',
        'periods',
        'get_count',
        'get_price',
        'is_test',
        'is_active',
        'get_published_jalali'
    ]
    list_filter = [
        'country',
        'periods'
    ]

    search_fields = [
        'name',
        'country'
        'id',
        'price'
    ]

    autocomplete_fields = ['country']

    @admin.display(description='مقدار گیگ', ordering='published')
    def get_count(self, obj):
        return obj.get_count()

    @admin.display(description='تاریخ ایجاد', ordering='published')
    def get_published_jalali(self, obj):
        return datetime2jalali(obj.published)

    @admin.display(description='مبلغ', ordering='price')
    def get_price(self, obj):
        return "{:,} تومان".format(int(obj.price))
