from django.db import models
from django.utils import timezone

from models.user.models import UserModel


class Transaction(models.Model):
    amount = models.IntegerField(verbose_name="مبلغ", help_text="تومان")
    track_id = models.TextField(null=True, blank=True, verbose_name="کد رهگیری")
    card_id = models.CharField(max_length=128, null=True, blank=True, verbose_name="شماره حساب")

    TYPE_CHOICES = (
        ('cost', 'هزینه'),
        ('order', 'سفارش'),
        ('wallet', 'کیف پول'),
        ('referral', 'بازاریابی'),
        ('crypto', 'رمز ارز'),
        ('card', 'کارت به کارت'),
    )
    type = models.CharField(max_length=64, choices=TYPE_CHOICES, default='wallet', verbose_name="روش پرداخت")

    STATUS_CHOICES = (
        ('pending', 'درانتظار پرداخت'),
        ('payed', 'پرداخت شده'),
        ('canceled', 'کنسل شده'),
        ('suspended', 'معلق'),
    )
    status = models.CharField(choices=STATUS_CHOICES, max_length=32, default="pending", verbose_name="وضعیت")
    user = models.ForeignKey(
        UserModel, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="کاربر"
    )
    published = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ انتشار"
    )
    created = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-published',)
        verbose_name = "تراکنش"
        verbose_name_plural = "تراکنشات"
