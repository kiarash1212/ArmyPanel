from django.contrib import admin
from jalali_date import datetime2jalali
from jalali_date.admin import ModelAdminJalaliMixin
from rangefilter2.filter import DateRangeFilter
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME

from models.ticket.models import Ticket, Answer


class AnsweringInline(ModelAdminJalaliMixin, admin.TabularInline):
    model = Answer
    extra = 1
    fields = ['message', 'side', 'image', 'get_published_jalali']
    readonly_fields = ['get_published_jalali', 'side']

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description='تاریخ ایجاد', ordering='published')
    def get_published_jalali(self, obj):
        return datetime2jalali(obj.published)


@admin.action(description="بستن تیکت های پاسخ داده شده")
def close_answereds(modeladmin, request, queryset):
    queryset.filter(status__exact="answered").update(status="closed")


@admin.register(Ticket)
class TicketAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    inlines = [AnsweringInline, ]
    list_display = [
        'subject',
        'order',
        'get_service_country',
        'get_service_server',
        'user',
        'status',
        'get_published_jalali',
    ]

    list_filter = [
        'subject',
        'status',
        ('published', DateRangeFilter),
        'published'
    ]

    search_fields = [
        'user__telegram_id',
        'user__telegram_username',
        'subject',
    ]

    actions = [close_answereds]

    autocomplete_fields = ['user', 'order']
    readonly_fields = ['order', 'user', 'request', 'subject', 'published', "image_tag"]

    @admin.display(description='تاریخ ایجاد', ordering='published')
    def get_published_jalali(self, obj):
        return datetime2jalali(obj.published)

    @admin.display(description='کشور', ordering='order')
    def get_service_country(self, obj):
        try:
            if obj.order:
                return obj.order.service.country.name
        except:return "-"
        return "-"

    @admin.display(description='سرور', ordering='order')
    def get_service_server(self, obj):
        if obj.order:
            server = getattr(obj.order.node, 'server', None)
            if server:
                return server.name
        return "-"

    def changelist_view(self, request, extra_context=None):
        if 'action' in request.POST and request.POST.get("action") == "close_answereds":
            if not request.POST.getlist(ACTION_CHECKBOX_NAME):
                post = request.POST.copy()
                for u in Ticket.objects.all():
                    post.update({ACTION_CHECKBOX_NAME: str(u.id)})
                request._set_post(post)
        return super(TicketAdmin, self).changelist_view(request, extra_context)