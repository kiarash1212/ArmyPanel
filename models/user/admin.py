from admincharts.admin import AdminChartMixin
from admincharts.utils import months_between_dates
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from jalali_date.admin import ModelAdminJalaliMixin
from rangefilter2.filter import DateRangeFilter

from models.user.models import UserModel


@admin.register(UserModel)
class UserAdmin(ModelAdminJalaliMixin, BaseUserAdmin):
    list_display = ('telegram_id', 'telegram_username', 'balance', 'is_staff', 'is_active')
    list_filter = (
        ('published', DateRangeFilter),
        'is_staff',
    )
    search_fields = [
        'telegram_id',
        'telegram_username'
    ]
    fieldsets = []

    actions = ['make_ban']

    list_chart_type = "bar"
    list_chart_options = {"aspectRatio": 6}



    @admin.action(description="غیرفعال کردن کاربر")
    def make_ban(self, request, queryset):
        queryset.update(is_active=False)
