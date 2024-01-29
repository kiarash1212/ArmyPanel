from django.contrib import admin
from jalali_date import datetime2jalali
from jalali_date.admin import ModelAdminJalaliMixin
from rangefilter2.filter import DateRangeFilter
from utils.telegram.message import send_message_telegram
from models.order.models import Order, Discount, ValueMonitoring
from utils.api.account import delete_account
class ValueMonitoringInline(ModelAdminJalaliMixin, admin.TabularInline):
    model = ValueMonitoring
    extra = 0
    fields = ['get_upload', 'get_download', 'order', 'get_published_jalali']
    readonly_fields = ['get_upload', 'get_download', 'order', 'get_published_jalali']

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='تاریخ ایجاد', ordering='published')
    def get_published_jalali(self, obj):
        return datetime2jalali(obj.published)

    @admin.display(description='آپلود', ordering='published')
    def get_upload(self, obj):
        return int(obj.upload)

    @admin.display(description='دانلود', ordering='published')
    def get_download(self, obj):
        return int(obj.download)

@admin.action(description="خذف کانفیگ ها روی سرور")
def delete_orders(modeladmin, request, queryset):

    orders = queryset.objects.all()

    for obj in orders:
        delete_account(obj.node.server.address, obj.account.provider_id)

@admin.register(Order)
class OrderAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    inlines = [ValueMonitoringInline, ]
    list_display = [
        'id',
        'get_published_jalali',
        'get_total',
        'get_price',
        'service',
        'get_expired_date_jalali',
        'user',
        'discount',
        'enable',
        'is_test_config',
    ]

    search_fields = [
        'id',
        'user__telegram_id',
        'user__telegram_username',
        'service__name'
    ]
    list_filter = (
        ('expired_date', DateRangeFilter),
        'expired_date',
        'is_test_config',
        'service',
        'enable',
        ('published', DateRangeFilter)
    )
    actions = [delete_orders]
    autocomplete_fields = ['user', 'service', 'node', 'discount']
    readonly_fields = ['up_obj', 'down_obj', 'total_obj', 'price_obj', 'discount', 'published']
    exclude = ['settings', 'is_test_config', 'published', 'up', 'down', 'total', 'price']

    @admin.display(description='آپلود', ordering='published')
    def up_obj(self, obj):
        return f"{int(obj.up)} مگابایت"

    @admin.display(description='دانلود', ordering='published')
    def down_obj(self, obj):
        return f"{int(obj.down)} مگابایت"

    @admin.display(description='مجموع', ordering='published')
    def total_obj(self, obj):
        return f"{int(obj.total)} مگابایت"

    @admin.display(description='هزینه', ordering='published')
    def price_obj(self, obj):
        return "{:,} تومان".format(int(obj.price))

    @admin.display(description='تاریخ ایجاد', ordering='published')
    def get_published_jalali(self, obj):
        return datetime2jalali(obj.published)

    @admin.display(description='تاریخ انقضا', ordering='expired_date')
    def get_expired_date_jalali(self, obj):
        if obj.expired_date:
            return datetime2jalali(obj.expired_date)
        return "-"

    @admin.display(description='مبلغ', ordering='price')
    def get_price(self, obj):
        return "{:,} تومان".format(int(obj.price))

    @admin.display(description='حجم مصرفی', ordering='total')
    def get_total(self, obj):
        if obj.total / 1024 >= 1:
            return "{:.2f} گیگابایت".format(obj.total / 1024)
        return "{:.2f} مگابایت".format(obj.total)

    def response_add(self, request, obj, post_url_continue=None):
        if obj.telegram_id:
            try:
                send_message_telegram(obj.telegram_id[0], """
                            کانفیگ سفارش شماره {} شما: 
                            <code>{}</code>
                            """.format(obj.pk, obj.config))
            except:pass
        return super().response_add(request, obj, post_url_continue)

@admin.register(Discount)
class DiscountAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = [
        'id',
        'code',
        'amount',
        'count',
        'get_expired_jalali',
        'get_published_jalali'
    ]
    list_filter = [
        'published',
        'expired'
    ]
    search_fields = ['code']

    autocomplete_fields = ['service', 'country', 'users']

    @admin.display(description='تاریخ ایجاد', ordering='published')
    def get_published_jalali(self, obj):
        return datetime2jalali(obj.published)

    @admin.display(description='تاریخ انقضا', ordering='expired')
    def get_expired_jalali(self, obj):
        if obj.expired:
            return datetime2jalali(obj.expired)
        return "-"
