from django.db import models
from django.utils import timezone
from solo.models import SingletonModel

from utils.api.token import check_token_status, get_new_token
from django.contrib.postgres.fields import ArrayField

class BaseModel(models.Model):
    provider_id = models.IntegerField(verbose_name="آیدی سرویس دهنده")
    name = models.CharField(max_length=64, verbose_name="نام")

    is_active = models.BooleanField(verbose_name="فعال/غیر فعال", default=False)

    published = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ انتشار"
    )
    created = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Server(BaseModel):
    address = models.URLField(verbose_name="آدرس پنل")
    username = models.CharField(max_length=6128, verbose_name="نام کاربری")
    password = models.CharField(max_length=6128, verbose_name="کلمه عبور")

    country = models.ForeignKey("service.Country", related_name="server_country", on_delete=models.SET_NULL, null=True,
                                blank=True, verbose_name="کشور")

    token = models.TextField(null=True, blank=True, verbose_name="توکن")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-published',)
        verbose_name = "سرور"
        verbose_name_plural = "سرور ها"

    def get_token(self):
        if self.check_token_status():
            return self.token
        else:
            if self.renew_token():
                return self.token
        return None

    def check_token_status(self):
        result = check_token_status(self)
        if result['type'] == 'error':
            return False
        else:
            return True

    def renew_token(self):
        result = get_new_token(self)
        if result['type'] == 'success':
            self.token = result['data']['token']
            self.save(update_fields=['token'])
            return True
        else:
            return False


class Node(BaseModel):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, verbose_name="سرور", related_name="nodes")
    url = models.CharField(max_length=254, verbose_name="آدرس کانکشن", null=True, blank=True)
    domain = models.CharField(max_length=128, verbose_name="دامنه", null=True, blank=True)
    port = models.IntegerField(verbose_name="پورت", null=True, blank=True)
    type = models.CharField(max_length=64, verbose_name="نوع", null=True, blank=True)

    max_value = models.IntegerField(default=200, verbose_name="حداکثر مقدار حجم")
    locked_date = models.DateTimeField(verbose_name="تاریخ قفل شدن", null=True, blank=True)

    is_test = models.BooleanField(default=False, verbose_name="آیا نود اکانت تست است ؟")

    def __str__(self):
        return "{} - {}".format(self.name, self.server.name)

    class Meta:
        ordering = ('-published',)
        verbose_name = "نود"
        verbose_name_plural = "نود ها"


class Account(models.Model):
    provider_id = models.IntegerField(null=True, blank=True, verbose_name="آیدی سرویس دهنده")

    username = models.CharField(max_length=128, verbose_name="نام کاربری")
    password = models.CharField(max_length=254, verbose_name="کلمه عبور")

    token = models.TextField(null=True, blank=True, verbose_name="توکن")

    is_active = models.BooleanField(default=True, verbose_name="فعال یا غیرفعال")

    published = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ انتشار"
    )
    created = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-published',)
        verbose_name = "اکانت"
        verbose_name_plural = "اکانت ها"

    def __str__(self):
        return f"{self.username}"

    def get_token(self, server):
        if self.check_token_status(server):
            return self.token
        else:
            if self.renew_token(server):
                return self.token
        return None

    def check_token_status(self, server):
        result = check_token_status(server, self)
        if result['type'] == 'error':
            return False
        else:
            return True

    def renew_token(self, server):
        result = get_new_token(server, self)
        if result['type'] == 'success':
            self.token = result['data']['token']
            self.save(update_fields=['token'])
            return True
        else:
            return False


class SiteConfiguration(SingletonModel):
    site_name = models.CharField(max_length=255, default='اشتراک ویژه', verbose_name="نام ربات")
    maintenance_mode = models.BooleanField(default=False, verbose_name="حال بروزرسانی")

    card_number = models.CharField(max_length=64, verbose_name="شماره کارت واریز")
    wepad_mobile = models.CharField(max_length=64, verbose_name="شماره ویپاد")
    wepad_token = models.CharField(null=True, blank=True, max_length=64, verbose_name="توکن ویپاد")
    wepad_code = models.CharField(max_length=64, null=True, blank=True, verbose_name="کد ورود ویپاد")

    crypto_wallet = models.CharField(null=True, blank=True, max_length=128, verbose_name="آدرس کیف پول ترون")
    tron_price = models.FloatField(default=1, verbose_name="قیمت هر واحد ترون")

    min_deposit = models.IntegerField(default=0, verbose_name="کمترین مقدار واریز")
    max_deposit = models.IntegerField(default=1000000, verbose_name="بیشترین مقدار واریز")

    referral_count = models.IntegerField(default=10, verbose_name="درصد کارمزد بازاریابی")

    validate_card_time = models.IntegerField(default=3, verbose_name="مدت زمان بررسی تراکنش کارت (دقیقه)")
    card_ban_time = models.IntegerField(default=15, verbose_name="مدت عدم واریز کارت (دقیقه)")
    ticket_count = models.IntegerField(default=1, verbose_name="تعداد تیکت های هم زمان")

    card_deposit_time = models.CharField(
        default="3-3",
        max_length=32,
        verbose_name="محدودیت ساعت واریز کارت به کارت", help_text="مانند : 0-7 (از 0بامداد تا ساعت 7 صبح)"
    )

    alarm_time = models.CharField(
        default="3-3",
        max_length=32,
        verbose_name="قانون آلارم اتمام سرویس", help_text="مانند : 3-3 (سه روز قبل و بعد)"
    )
    alarm_value = models.IntegerField(
        default=30,
        max_length=32,
        verbose_name="قانون آلارم حجم اتمام سرویس", help_text="درصد"
    )

    account_test_period = models.IntegerField(verbose_name="مدت زمان اکانت تست", default=10)
    account_test_value = models.IntegerField(verbose_name="مقدار حجم اکانت تست", default=100)
    account_test_limition = models.IntegerField(verbose_name="تعداد اکانت های تست قابل مجاز", default=1)

    join_channels = models.TextField(verbose_name="کانال های ادد اجباری", blank=True, null=True)
    admins_TIDS = models.TextField(verbose_name="تلگرام آیدی ادمین ها", blank=True, null=True)
    supports_TIDS = models.TextField(verbose_name="تلگرام آیدی پشتیبان ها", blank=True, null=True)

    ext_service_role = models.CharField(
        max_length=32,
        verbose_name="قانون تمدید سرویس", help_text="مانند : 3-3 (سه روز قبل و بعد)"
    )

    def __str__(self):
        return "تنظیمات ربات"

    class Meta:
        verbose_name = "تنظیمات کلی"
