import datetime
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

import requests.exceptions
from django.db import models
from django.db.models import Sum, Q
from django.utils import timezone
from jdatetime import datetime as jdatetime

from models.configure.models import Account, Node, Server
from models.service.models import Service, Country
from models.user.models import UserModel
from utils.api.account import create_account, delete_account
from utils.api.node import get_config_url
import string
import random


class Discount(models.Model):
    code = models.TextField(verbose_name="کد تخفیف")
    count = models.IntegerField(default=1, verbose_name="تعداد")
    amount = models.FloatField(default=1, verbose_name="درصد")

    users = models.ManyToManyField(
        UserModel,
        null=True,
        blank=True,
        verbose_name="کاربر ها",
        help_text="در صورت انتخاب هیچ یک از کاربر ها یا سرویس ها پیام همگانی تلقی می شود."
    )

    service = models.ManyToManyField(
        Service,
        null=True,
        blank=True,
        verbose_name="سرویس ها",
        help_text="در صورت اینکه می خواهید به کاربر یک سرویس پیام ارسال کنید سرویس مورد نظر خود را انتخاب نمایید"
    )
    country = models.ManyToManyField(
        Country,
        null=True,
        blank=True,
        verbose_name="کشور ها"
    )

    expired = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ انفضا"
    )

    published = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ انتشار"
    )
    created = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-published',)
        verbose_name = "کد تخفیف"
        verbose_name_plural = "کد های تخفیف"

    def __str__(self):
        return f"کد: {self.code}"


class Order(models.Model):
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="سرویس")
    user = models.ForeignKey(UserModel, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="کاربر")
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="کد تخفیف")
    node = models.ForeignKey(
        Node,
        on_delete=models.SET_NULL,
        related_name="order_node_model",
        verbose_name="نود کانفیگ",
        null=True,
        blank=True
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="اکانت کانفیگ",
    )

    user_pass = models.CharField(max_length=10, default='', verbose_name="یوزرنیم")
    price = models.FloatField(verbose_name="هزینه", default=0)

    up = models.FloatField(verbose_name="آپلود", default=0)
    down = models.FloatField(verbose_name="دانلود", default=0)
    total = models.FloatField(verbose_name="کل مصرفی", default=0)

    settings = models.TextField(verbose_name="تنظیمات", null=True, blank=True)
    config = models.TextField(verbose_name="کانفیگ اتصال", null=True, blank=True)

    provider_id = models.IntegerField(verbose_name="آیدی پنل", editable=False, null=True, blank=True)
    expired_date = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ انقضا")
    enable = models.BooleanField(default=False, verbose_name="فعال یا غیرفعال")

    alarm_send_data = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ ارسال آلارم")
    is_test_config = models.BooleanField(default=False, verbose_name="آیا کانفیگ تست می باشد ؟")
    # is_archived = models.BooleanField(default=False, verbose_name="بایگانی شده")

    published = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ انتشار"
    )
    created = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-published',)
        verbose_name = "سفارش"
        verbose_name_plural = "سفارشات"

    def __str__(self):
        return "{}".format(self.id)

    def published_shamsi(self):
        if self.published:
            return jdatetime.fromgregorian(datetime=self.published).strftime('%Y/%m/%d')
        return ""

    def expired_date_shamsi(self):
        if self.expired_date:
            return jdatetime.fromgregorian(datetime=self.expired_date).strftime('%Y/%m/%d')
        return ""

    def reset_data(self):
        self.up = 0
        self.down = 0
        self.total = 0
        self.alarm_send_data = None

        self.save()

        return True

    def create_config(self, ip_server=False, is_extension=False):
        nodes = Node.objects.filter(
            Q(locked_date__lt=timezone.now()) | Q(locked_date__exact=None),
            is_active=True,
            server__country=self.service.country,
            server__is_active=True,
            is_test=self.service.is_test
        )
        if ip_server:
            nodes = nodes.filter(server_id=self.node.server_id)

        node, account, node_fulled = None, None, False
        user_pass = self.user_pass or ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase, k=8))

        for item in nodes:
            total_count = Order.objects.filter(service__isnull=False, enable=True, node_id=item.id).aggregate(
                total_count=Sum('service__count')
            )['total_count']
            if not total_count:
                total_count = 0

            if total_count + self.service.count <= item.max_value:
                node = item
                if total_count + self.service.count == item.max_value:
                    node_fulled = True
                continue

        if node:
            expire_data = timezone.now() + datetime.timedelta(days=self.service.periods.value)
            if not node.locked_date and node_fulled:
                node.locked_date = expire_data
                node.save(update_fields=['locked_date'])

            server = node.server
            self.node = node

            try:
                # Fetch new token for login
                if not Account.objects.filter(username=user_pass, password=user_pass).exists():
                    server.get_token()

                    result = create_account(
                        server,
                        {
                            'username': user_pass,
                            'password': user_pass,
                            'value': int(self.service.count * 1024),
                            'expireTime': int(expire_data.timestamp() * 1000)
                        }
                    )

                    if 'type' in result:
                        if result['type'] == 'success':
                            account = Account.objects.create(
                                username=user_pass,
                                password=user_pass,
                            )
                else:
                    account = Account.objects.get(username=user_pass)
                    delete_response = delete_account(server, account.provider_id)

                    if 'type' in delete_response:
                        if delete_response['type'] != 'success':
                            return False
                    else:
                        return False

                    result = create_account(server,
                        {
                            'username': user_pass,
                            'password': user_pass,
                            'value': int(self.service.count * 1024),
                            'expireTime': int(expire_data.timestamp() * 1000)
                        }
                    )

                    if 'type' in result:
                        if result['type'] == 'success':
                            account.provider_id = None
                            account.token = None
                            account.save()
                    else:
                        return False
            except requests.exceptions.ConnectionError:
                return False

            if account:
                account.get_token(server)
                if account.get_token(server):
                    node_response = get_config_url(server, node, account)
                else:
                    return False

                if 'data' not in node_response:
                    return False
                if not node_response['data']:
                    return False

                parsed_url = urlparse(node_response['data'])
                query_params = parse_qs(parsed_url.query)
                # if 'flow' in query_params:
                #     del query_params['flow']
                #     comment
                new_query = urlencode(query_params, doseq=True).replace('%2F', "/")

                new_url_parts = parsed_url._replace(query=new_query)
                new_address = urlunparse(new_url_parts)

                address, name = new_address.split("#")

                self.config = f"{address}#user{user_pass}_{self.service.count}GB_{self.service.periods.value}DAYS_{name}_V2RayArmy"

                self.account = account
                self.user_pass = user_pass

                self.save(update_fields=['config', 'node', 'account', 'user_pass'])
        else:
            if not is_extension:
                self.delete()
            return False

        self.set_expired_date()
        self.make_enable()
        return self.config

    def extension_config(self):
        self.make_enable()
        return True

    def make_enable(self):
        self.enable = True
        self.save(update_fields=['enable'])

    def make_disable(self):
        self.enable = False
        self.save(update_fields=['enable'])

    def set_expired_date(self):
        self.expired_date = timezone.now() + datetime.timedelta(days=self.service.periods.value)
        self.save(update_fields=['expired_date'])


class ValueMonitoring(models.Model):
    download = models.FloatField(verbose_name="دانلود")
    upload = models.FloatField(verbose_name="آپلود")

    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="سفارش")

    published = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ انتشار"
    )
    created = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-published',)
        verbose_name = "گزارش مصرف حجم"
        verbose_name_plural = "مانیتورینگ مصرف حجم"

    def __str__(self):
        return ""
