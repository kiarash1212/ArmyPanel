from datetime import timedelta

from django.core.management import BaseCommand
from django.utils import timezone

from bot.context.messages import ORDER_VALUE_ALARM_MSG
from models.configure.models import SiteConfiguration
from models.order.models import Order
from utils.telegram.message import send_message


class Command(BaseCommand):
    def handle(self, *args, **options):
        orders = Order.objects.filter(enable=True)
        configure = SiteConfiguration.get_solo()

        ext_service_role = configure.ext_service_role.split('-')
        today = timezone.now()
        date_day_later = timedelta(days=int(ext_service_role[0]))
        date_day_ago = timedelta(days=int(ext_service_role[1]))

        for item in orders:
            used_mb = item.total / (1024 * 1024)
            total_mb = item.service.count * 1024
            free_mb = total_mb - used_mb

            base_msg = ORDER_VALUE_ALARM_MSG

            if (total_mb * configure.alarm_value) / 100 > free_mb:
                base_msg += f"از حجم سرویس شما کمتر از {configure.alarm_value}🔆 درصد باقی مانده است.\n"
            if item.expired_date:
                if item.expired_date + date_day_later > today and item.expired_date < today:
                    base_msg += "🔆 کمتر از 3 روز تا انقضا سرور شما باقی است\n"
                if item.expired_date > today and item.expired_date - date_day_ago < today:
                    base_msg += "🔆 زمان انقضا سرویس شما گذشته است.\n"

            if base_msg != ORDER_VALUE_ALARM_MSG:
                send_message(
                    text=base_msg.format(
                        f"{item.service.country.key.upper()}_{item.service.periods.value}D_{item.service.user_count}U_{item.service.count}G_ID{item.id}"
                    ),
                    chat_id=item.user.telegram_id
                )
        self.stdout.write(
            self.style.SUCCESS('Successfully update contract list')
        )
