import json
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configbot.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from models.user.models import UserModel

file = open("users.json")

data = json.load(file)

for item in data['data']:
    user_model, is_created = UserModel.objects.get_or_create(
        telegram_id=item['id'],
    )

    user_model.balance = balance = int(item['wallet'])
    user_model.save()
