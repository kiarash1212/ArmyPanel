import requests
import io
from django.db import models
from django.utils import timezone

from jdatetime import datetime as jdatetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from bot.context.messages import TICKET_MSG, TICKET_CLOSED_MSG, TICKET_ALERT_MSG
from configbot.settings import TELEGRAM_TOKEN
from models.configure.models import SiteConfiguration
from models.order.models import Order
from models.service.models import Service
from models.user.models import UserModel

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from utils.telegram.message import send_message_telegram
from django.utils.html import mark_safe

class Ticket(models.Model):
    subject = models.CharField(max_length=64, verbose_name="موضوع درخواست")
    request = models.TextField(verbose_name="درخواست")
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="سفارش")
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, verbose_name="کاربر")
    image = models.ImageField(upload_to="tickets_image", null=True, blank=True, verbose_name="تصویر")

    STATUS_CHOICES = (
        ("pending", "خوانده نشده"),
        ("suspended", "درحال پیگیری"),
        ("answered", "پاسخ داده شده"),
        ("closed", "بسته شده"),

    )
    status = models.CharField(choices=STATUS_CHOICES, default='pending', max_length=64, verbose_name="وضعیت")

    published = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ انتشار"
    )
    created = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-published',)
        verbose_name = "تیکت"
        verbose_name_plural = "تیکت ها"

    def __str__(self):
        return self.subject

    def published_shamsi(self):
        return jdatetime.fromgregorian(datetime=self.published).strftime('%Y/%m/%d')

    def image_tag(self):
        return mark_safe('<img src="/media/%s" max-width="150" max-height="150" />' % (self.image))

@receiver(pre_save, sender=Ticket, dispatch_uid="send_status_user")
def send_status_user(sender, instance, **kwargs):
    try:
        last_model = Ticket.objects.get(id=instance.id)
    except Ticket.DoesNotExist:
        return

    if last_model.status != instance.status:
        if instance.status == 'closed':
            api_url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
            try:
                requests.post(
                    api_url,
                    json={
                        'chat_id': instance.user.telegram_id,
                        'text': TICKET_CLOSED_MSG.format(
                            instance.id
                        ),
                        'parse_mode': 'html'
                    }
                )
            except Exception as e:
                pass

@receiver(post_save, sender=Ticket, dispatch_uid="send_ticket_alarm")
def send_ticket_alarm(sender, instance, created, **kwargs):
    if not created:return
    try:
        Ticket.objects.get(id=instance.id)
    except Ticket.DoesNotExist:
        return

    telegram_supports = [int(i) for i in (SiteConfiguration.get_solo().supports_TIDS or "").split('\n') if i]
    for admin in telegram_supports:
        try:
            send_message_telegram(admin, TICKET_ALERT_MSG.format(instance.user.username))
        except Exception as e:print(e)

class Answer(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, verbose_name="تیکت")
    message_id = models.IntegerField(verbose_name="آیدی پیام", null=True, blank=True)
    message = models.TextField(verbose_name="پیام")
    image = models.ImageField(upload_to="tickets_image", null=True, blank=True, verbose_name="تصویر")
    side = models.CharField(
        choices=(
            ('user', 'کاربر'),
            ('support', 'پشتیبان'),
        ),
        default='support',
        max_length=64,
        verbose_name="ارسال کننده"
    )

    published = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ انتشار"
    )
    created = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.message

    def image_tag(self):
        return mark_safe('<img src="/media/%s" max-width="100" max-height="100" />' % (self.image))

    class Meta:
        verbose_name = "پاسخ"
        verbose_name_plural = "پاسخ ها"


@receiver(post_save, sender=Answer, dispatch_uid="send_answer_to_user")
def send_answer_to_user(sender, instance, **kwargs):
    print('saving....', instance.ticket.pk)
    if instance.side == "support":
        image = io.BytesIO(instance.image.file.file.read()) if instance.image else None
        if not instance.message_id:
            send_message_telegram(instance.ticket.user.telegram_id, TICKET_MSG.format(
                            instance.ticket.id,
                            instance.message
                        ), file=image, inline_keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("ارسال پیام",callback_data=f"replyTicket_{instance.ticket.pk}")]]).to_dict())