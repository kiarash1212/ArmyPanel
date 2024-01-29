import random

from django.contrib import auth
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import PermissionDenied
from django.db import models
from django_jalali.db import models as jmodels
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def _user_has_perm(user, perm, obj):
    for backend in auth.get_backends():
        if not hasattr(backend, 'has_perm'):
            continue
        try:
            if backend.has_perm(user, perm, obj):
                return True
        except PermissionDenied:
            return False
    return False


def _user_has_module_perms(user, app_label):
    for backend in auth.get_backends():
        if not hasattr(backend, 'has_module_perms'):
            continue
        try:
            if backend.has_module_perms(user, app_label):
                return True
        except PermissionDenied:
            return False
    return False


class UserManager(BaseUserManager):
    def create_user(self, username, telegram_id, password=None):
        if not username:
            raise ValueError('Users must have an username')

        user = self.model(
            username=username,
            telegram_id=telegram_id
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, telegram_id, username, password=None):
        user = self.create_user(
            username=username, telegram_id=telegram_id, password=password,
        )
        user.is_admin = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class UserModel(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        max_length=300,
        unique=True,
        blank=True,
        null=True,
        verbose_name="نام کاربری"
    )
    first_name = models.CharField(max_length=128, null=True, blank=True, verbose_name="نام")
    last_name = models.CharField(max_length=64, null=True, blank=True, verbose_name="نام خانوادگی")

    telegram_id = models.CharField(max_length=125, unique=True, verbose_name="شماره تلگرام")
    telegram_username = models.CharField(max_length=125, null=True, blank=True, verbose_name="آیدی تلگرام")

    balance = models.IntegerField(default=0, verbose_name="موجودی")

    mobile = models.CharField(
        max_length=12,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("تلفن همراه"),
    )

    data = models.TextField(default="{}")

    alarm_count = models.IntegerField(default=0, verbose_name="اخطار های دریافتی")
    alarm_date = models.DateTimeField(null=True, blank=True, verbose_name="زمان آخرین اخطار")

    parent = models.CharField(max_length=128, null=True, blank=True, verbose_name="معروف")
    refal = models.BigIntegerField(unique=True, null=True, blank=True, verbose_name="کد دعوت")
    refal_income = models.IntegerField(default=0, verbose_name="درآمد")
    refal_count = models.IntegerField(default=0, verbose_name="تعداد زیر مجموعه ها")

    is_mobile_accepted = models.BooleanField(default=False, verbose_name=_("تلفن همراه تایید شده است ؟"))

    save_log = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    published = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ انتشار"
    )
    created = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    recovery = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['telegram_id']

    class Meta:
        permissions = (
            ("can_see_admin_page", "Can see admin page"),
        )
        ordering = ('-published',)
        verbose_name = _("حساب کاربری")
        verbose_name_plural = _("حساب های کاربری")

    def __str__(self):
        return "{} - {}".format(self.telegram_id, self.telegram_username)

    def save(self, *args, **kwargs):
        self.username = self.telegram_id
        data = super(UserModel, self).save(*args, **kwargs)
        if not self.refal:
            self.refal = self.telegram_id
        return data


class IPLog(models.Model):
    ip = models.GenericIPAddressField(verbose_name=_("آی پی"))
    device = models.CharField(max_length=128, verbose_name=_("دستگاه"))
    browser = models.CharField(max_length=128, verbose_name=_("مرورگر"))
    published = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ ایجاد"
    )
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, verbose_name=_("کاربر"))
    created = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-published',)
        verbose_name = _("لاگ")
        verbose_name_plural = _("لاگ ها")

    def __str__(self):
        return "{}".format(self.ip)
