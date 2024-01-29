from django.contrib import admin
from jalali_date import datetime2jalali
from jalali_date.admin import ModelAdminJalaliMixin

from models.emergency.models import Emergency


@admin.register(Emergency)
class EmergencyAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = [
        'server',
        'emergency_node',
        'value',
        'day',
        'is_lunched',
        'get_published_jalali',
    ]

    list_filter = [
        'published',
        'server',
        'emergency_node',
        'is_lunched'
    ]

    autocomplete_fields = ['server', 'emergency_node']
    readonly_fields = ['is_lunched', 'accounts']

    @admin.display(description='تاریخ ایجاد', ordering='published')
    def get_published_jalali(self, obj):
        return datetime2jalali(obj.published)
