from django.db import models
from django.utils import timezone

from models.configure.models import Server
from models.service.models import Service, Country
from models.user.models import UserModel


class Notification(models.Model):
    text = models.TextField(verbose_name="متن پیام")

    all_user = models.BooleanField(default=False, verbose_name="یا پیام همگانی باشد ؟")

    users = models.ManyToManyField(
        UserModel,
        null=True,
        blank=True,
        verbose_name="کاربر ها",
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
    server = models.ManyToManyField(
        Server,
        null=True,
        blank=True,
        verbose_name="سرور ها"
    )
    published = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ انتشار"
    )
    created = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-id',)
        verbose_name = "پیام"
        verbose_name_plural = "پیام ها"


from .signals import send_message
