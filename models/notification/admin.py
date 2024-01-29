from django.contrib import admin
from jalali_date import datetime2jalali
from jalali_date.admin import ModelAdminJalaliMixin
from rangefilter2.filter import DateRangeFilter

from models.notification.models import Notification


@admin.register(Notification)
class NotificationAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = [
        'id',
        'get_text',
        'get_published_jalali'
    ]
    list_filter = [
        ('published', DateRangeFilter),
        'published',
        'service',
    ]
    search_fields = ['id', 'text']
    autocomplete_fields = ['service', 'users', 'server', 'country']

    @admin.display(description='تاریخ ایجاد', ordering='published')
    def get_published_jalali(self, obj):
        return datetime2jalali(obj.published)

    @admin.display(description='متن پیام', ordering='text')
    def get_text(self, obj):
        if len(obj.text) >= 50:
            return f"{obj.text[:50]} ...."
        return f"{obj.text[:50]}"
