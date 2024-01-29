from django.apps import AppConfig


class NotificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'models.notification'
    verbose_name = "مرکز پیام"

    def ready(self):
        import models.notification.signals
