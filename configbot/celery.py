mport os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configbot.settings')

app = Celery('configbot')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
