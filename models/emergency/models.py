from django.db import models
from django.utils import timezone
from jalali_date.admin import ModelAdminJalaliMixin

from models.configure.models import Server, Node, Account


class Emergency(ModelAdminJalaliMixin, models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="source_server", verbose_name="سرور مبدا")
    emergency_node = models.ForeignKey(
        Node, on_delete=models.CASCADE,
        verbose_name="نود سرور جایگزین"
    )
    accounts = models.ManyToManyField(Account,null=True, blank=True, verbose_name="کانفیگ ها ساخته شده")

    value = models.IntegerField(verbose_name="حجم (GB)")
    day = models.IntegerField(verbose_name="مدت زمان (روز)")

    is_lunched = models.BooleanField(default=False, verbose_name="اجرا شده است ؟")

    published = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ انتشار"
    )
    created = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-id',)
        verbose_name = "کانفیگ اضطراری"
        verbose_name_plural = "کانفیگ های اضطراری"

    def __str__(self):
        return f"کانفیگ سرور {self.server.name} بجای سرور {self.emergency_node.server.name}"
