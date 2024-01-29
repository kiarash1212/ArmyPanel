from django.apps import AppConfig


class EmergencyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'models.emergency'

    verbose_name = "اضطراری"

    def ready(self):
        from .signals import send_configs
