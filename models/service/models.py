from django.db import models
from django_jalali.db import models as jmodels
from django.utils import timezone
from django.db.models import Sum
from models.configure.models import Node, Server


class BaseModel(models.Model):
    name = models.CharField(max_length=64, verbose_name="نام")

    is_active = models.BooleanField(default=True, verbose_name="فعال/غیرفعال")

    published = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ انتشار"
    )
    created = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Country(BaseModel):
    key = models.CharField(max_length=32, verbose_name="کلید")

    class Meta:
        ordering = ('-published',)
        verbose_name = "کشور"
        verbose_name_plural = "کشور ها"

    def get_country_remaining_capacity(self):

        total_capacity = 0
        total_traffic = 0
        for server in self.server_country.all():
            total_capacity += (server.nodes.aggregate(totalCapacity=Sum("max_value"))['totalCapacity'] or 0) * 1000
            for config in server.nodes.all():
                total_traffic += config.order_node_model.aggregate(totalTraffic=Sum("total"))['totalTraffic'] or 0

        return (total_capacity - total_traffic) / 1000

class Period(BaseModel):
    value = models.IntegerField(verbose_name="تعداد روز")

    class Meta:
        ordering = ('-published',)
        verbose_name = "دوره"
        verbose_name_plural = "دوره ها"


class Service(BaseModel):
    count = models.FloatField(verbose_name="مقدار گیگ")
    user_count = models.IntegerField(verbose_name="تعداد کاربر")
    price = models.IntegerField(verbose_name="هزینه (تومان)")
    cost = models.IntegerField(verbose_name="هزینه نگه داری (تومان)")

    price_multi_discount = models.IntegerField(verbose_name="درصد تخفیف فروش عمده")
    price_discount = models.IntegerField(verbose_name="درصد تخفیف تمدید ویژه")
    price_normal_discount = models.IntegerField(verbose_name="درصد تخفیف تمدید معمولی")
    price_ip_discount = models.IntegerField(verbose_name="درصد افزایش نرخ تمدید آی پی")

    is_test = models.BooleanField(default=False, verbose_name="سرویس تست")

    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        related_name="country_model",
        verbose_name="کشور",
        null=True,
        blank=True
    )
    periods = models.ForeignKey(
        Period,
        on_delete=models.SET_NULL,
        related_name="periods_model",
        verbose_name="زمان ها",
        null=True,
        blank=True
    )

    class Meta:
        ordering = ('-published',)
        verbose_name = "سرویس"
        verbose_name_plural = "سرویس ها"

    def __str__(self):
        return "{} - {} _ {}".format(
            self.country,
            self.count,
            self.user_count
        )

    def h_toman(self):
        return int(self.price / 1000)

    def get_count(self):
        return int(self.count)
