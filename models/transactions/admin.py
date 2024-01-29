from django.contrib import admin
from jalali_date import datetime2jalali
from jalali_date.admin import ModelAdminJalaliMixin
from rangefilter2.filter import DateRangeFilter

from models.transactions.models import Transaction


@admin.register(Transaction)
class TransactionAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = [
        'id',
        'get_amount',
        'user',
        'status',
        'type',
        'get_published_jalali'
    ]

    list_filter = [
        ('published', DateRangeFilter),
        'published',
        'status',
        'type',
    ]

    search_fields = [
        'track_id',
        'user__telegram_id',
        'user__telegram_username',
    ]

    autocomplete_fields = ['user']

    @admin.display(description='تاریخ ایجاد', ordering='published')
    def get_published_jalali(self, obj):
        return datetime2jalali(obj.published)

    @admin.display(description='مبلغ', ordering='amount')
    def get_amount(self, obj):
        return "{:,} تومان".format(int(obj.amount))
