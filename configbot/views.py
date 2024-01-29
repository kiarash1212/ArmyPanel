import datetime
import json
from datetime import timedelta

import jdatetime
import requests
from django.db.models import Sum, Count, F, FloatField, Q
from django.db.models.functions import TruncDate, Coalesce
from django.http import HttpResponse
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from excel_response import ExcelResponse

from bot.context.messages import ORDER_VALUE_ALARM_MSG
from models.configure.models import SiteConfiguration, Server, Node
from models.order.models import Order, ValueMonitoring
from models.ticket.models import Ticket
from models.service.models import Country
from models.transactions.models import Transaction
from utils.api.account import information_account, search_account
from utils.api.node import fetch_all_nodes
from utils.card.main import get_data_sms
from utils.report.transaction import get_transaction_report, get_today_transactions, get_month_transactions
from utils.telegram.message import send_message_telegram


class AppView(TemplateView):
    template_name = "app.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        daily_income, weekly_income, monthly_income, total_income = self.get_general_income()

        context.update({
            "general_income": {
                "daily": daily_income,
                "weekly": weekly_income,
                "monthly": monthly_income,
                "total": total_income,
            }
        })


        return context

    def get_general_income(self):
        return get_transaction_report(data=self)


class GenerateExelReport(View):
    def get(self, request):
        period = request.GET.get("period", 'daily')
        if period == "daily":
            listOf_transactions = get_today_transactions()
        else:
            listOf_transactions = get_month_transactions()
        # ایجاد دیکشنری حاوی داده‌ها

        fields = [i for i in Transaction._meta.fields if i.name != 'id']
        fields_names = [j.name for j in fields] + ['user_id']
        data = [
            [*[i.verbose_name for i in fields]],
        ] + [[i.__dict__[field] for field in i.__dict__ if field in fields_names] for i in listOf_transactions]


        daily_income, weekly_income, monthly_income, total_income = get_transaction_report(data=self)

        # ایجاد دیکشنری حاوی داده‌ها
        theReports = [
            ['', 'درآمد', 'هزینه', 'سود'],
            ['روزانه', daily_income['total'], daily_income['cost'], daily_income['profit']],
            ['هفتگی', weekly_income['total'], weekly_income['cost'], weekly_income['profit']],
            ['ماهانه', monthly_income['total'], monthly_income['cost'], monthly_income['profit']],
            ['بازده انتخابی', total_income['total'], total_income['cost'], total_income['profit']]
        ]

        for row, value in enumerate(theReports):
            data[row] += ['' for _ in range(5)] + value

        # ایجاد ExcelResponse
        response = ExcelResponse(data)

        # تنظیم نام فایل اکسل
        file_name = f"report_{timezone.now().date()}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'

        return response


class ChartView(TemplateView):
    template_name = "chart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        service_sales = Order.objects.filter(service__is_test=False).values("service__name").annotate(
            total_sales=Count("service")
        ).order_by("-total_sales")

        service_sales_data = [
            {"service": item["service__name"], "total_sales": item["total_sales"]} for item in service_sales
        ]

        service_sales_by_country = Country.objects.values('name',).annotate(
            total_sales=Count('country_model__order'),

        ).order_by('-total_sales')

        country_sales_data = [
            {'country': item['name'],
             'total_sales': item['total_sales']} for item in service_sales_by_country
        ]

        # استخراج داده‌های مرتبط از پایگاه داده
        data_by_date = Order.objects.annotate(date=TruncDate('published')).values('date').annotate(
            total_price=Sum('service__price'),
            total_cost=Sum('service__cost'),
            total_profit=Sum('service__price') - Sum('service__cost'),
        ).order_by('date')

        sales_data = [{'date': jdatetime.datetime.fromgregorian(date=item['date']).strftime('%Y-%m-%d'), 'total_price': item['total_price'],
                       'total_cost': item['total_cost'], 'total_profit': item['total_profit']} for item in data_by_date]

        total_active_orders = Order.objects.filter(enable=True).count()
        context.update({
            "service_sales_data": service_sales_data,
            "country_sales_data": country_sales_data,
            "sales_data": sales_data
        })
        return context


class ServerView(TemplateView):
    template_name = "server.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        server_data = Node.objects.filter(is_active=True).annotate(
            total_sold_volume=Coalesce(
                Sum('order_node_model__service__count'), 0,
                output_field=FloatField()
            ),
            total_consumption=Coalesce(
                Sum('order_node_model__total') / 1024,
                0,
                output_field=FloatField()
            ),
            total_server_volume=F('max_value'),
            server__address=F('server__name'),
            name__address=F('name'),
        ).values('server__address', 'name__address', 'total_server_volume', 'total_sold_volume', 'total_consumption', 'server__country__name')


        groupByCountry = {}

        for row in list(server_data):
            groupByCountry[row['server__country__name']] = groupByCountry.get(row["server__country__name"], []) + [row]

        context.update({
            "server_data": groupByCountry,
        })
        return context


@csrf_exempt
@require_http_methods(["POST"])
def my_view(request):
    text = str(request.POST.get("data"))

    if "واریز" in text:
        amount, date = get_data_sms(text)

        if amount and date:
            Transaction.objects.create(
                amount=amount / 10,
                type="card",
                published=date
            )

    return HttpResponse("OK")


@require_http_methods(["GET"])
def my_viesw(request):
    order = Order.objects.first()
    order.create_config()


@require_http_methods(["GET"])
def update_nodes_view(request):
    servers = Server.objects.filter(is_active=True)
    for item in servers:
        try:
            item.get_token()
            node_list = fetch_all_nodes(item)
        except:
            item.is_active = False
            item.save()
            continue

        node_list_model = Node.objects.filter(server_id=item.id).values_list('provider_id', flat=True)
        node_request_list = []

        for node in node_list["data"]["nodes"]:
            node_request_list.append(node["id"])
            if node["status"] == 1:
                item_model, is_create = Node.objects.get_or_create(provider_id=node["id"], name=node["name"],
                                                                   server_id=item.id)
                item_model.domain = node["domain"]
                item_model.port = node["port"]
                item_model.type = node["nodeTypeId"]

                item_model.is_active = True
                item_model.server = item
                item_model.save()
            else:
                try:
                    node_model = Node.objects.get(provider_id=node['id'], server_id=item.id)
                    node_model.is_active = False
                    node_model.save(update_fields=['is_active'])
                except Node.DoesNotExist:
                    pass

        result = [item for item in node_list_model if item not in node_request_list]
        for n in result:
            try:
                node_model = Node.objects.get(provider_id=n, server_id=item.id)
                node_model.is_active = False
                node_model.save(update_fields=['is_active'])
            except Node.DoesNotExist:
                pass

    return HttpResponse("OK")


@require_http_methods(["GET"])
def price_view(request):
    configure = SiteConfiguration.get_solo()
    try:
        url = "https://api.nobitex.ir/market/stats"
        payload = json.dumps({
            "srcCurrency": "trx",
            "dstCurrency": "rls"
        })
        headers = {
            'content-type': 'application/json',
        }
        response = requests.request("POST", url, headers=headers, data=payload).json()

        configure.tron_price = int(response['stats']['trx-rls']['bestBuy']) / 10

        configure.save(update_fields=['tron_price'])

    except KeyError as e:
        print(e)
        pass
    return HttpResponse("OK")

@require_http_methods(["GET"])
def update_tickets(request):
    today = timezone.today() - timedelta(hours=24)
    Ticket.objects.filter(status__exact="answered", update__lte=today).update(status="closed")

@require_http_methods(["GET"])
def account_view(request):
    orders = Order.objects.filter(enable=True)

    configure = SiteConfiguration.get_solo()

    ext_service_role = configure.ext_service_role.split('-')
    test_configs_expire_days = timedelta(days=int(configure.account_test_period))

    today = timezone.now()
    today = today.replace(hour=23, minute=59)
    date_day_later = timedelta(days=int(ext_service_role[0]))
    date_day_ago = timedelta(days=int(ext_service_role[1]))

    oneDayTimeDelta = timedelta(days=1)

    for item in orders:
        item = Order.objects.get(id=item.id)

        if item.node:
            server = item.node.server
        else:
            continue

        server.get_token()
        try:
            if item.account.provider_id:
                response = information_account(server, item.account.provider_id)
                item.up = int(response["data"]["upload"]) / 1048576
                item.down = int(response["data"]["download"]) / 1048576
                item.total = item.up + item.down
                item.save()

            else:
                response = search_account(server, item.account.username)

                if response["data"]["accounts"]:
                    account_data = response["data"]["accounts"][0]
                    item.account.provider_id = account_data["id"]

                    item.up = int(account_data["upload"]) / 1048576
                    item.down = int(account_data["download"]) / 1048576
                    item.total = item.up + item.down
                    item.account.save()
                    item.save()

            if item.is_test_config:
                if item.published + test_configs_expire_days < today:
                    item.delete()
            else:
                used_mb = item.total / (1024 * 1024)
                total_mb = item.service.count * 1024
                free_mb = total_mb - used_mb

                base_msg = ORDER_VALUE_ALARM_MSG

                if (total_mb * configure.alarm_value) / 100 > free_mb:
                    base_msg += f"از حجم سرویس شما کمتر از {configure.alarm_value}🔆 درصد باقی مانده است.\n"
                if item.expired_date:
                    if item.expired_date + date_day_later < today:
                        # item.delete()
                        item.make_disable()
                    #     delete from panel
                    elif item.expired_date < today and item.expired_date + date_day_later > today and (
                        today - item.expired_date < oneDayTimeDelta):
                        item.make_disable()
                    elif item.expired_date > today and item.expired_date - date_day_ago < today and (
                        item.expired_date - date_day_ago - today < oneDayTimeDelta):
                        base_msg += "🔆 کمتر از 3 روز تا انقضای سرور شما باقی است\n"

                if base_msg != ORDER_VALUE_ALARM_MSG:
                    send_message_telegram(
                        text=base_msg.format(
                            f"{item.service.country.key.upper()}_{item.service.periods.value}D_{item.service.user_count}U_{item.service.count}G_ID{item.id}"
                        ),
                        chat_id=item.user.telegram_id
                    )
        except:
            pass

        current_datetime = timezone.now()
        start_of_day = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = current_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)

        if not ValueMonitoring.objects.filter(
                order_id=item.id,
                published__gte=start_of_day,
                published__lte=end_of_day
        ):
            ValueMonitoring.objects.create(
                upload=item.up,
                download=item.down,
                order_id=item.id
            )

        for country in Country.objects.all():
            if country.get_country_remaining_capacity() < 200:
                for admin in (SiteConfiguration.get_solo().admins_TIDS):
                    try:
                        send_message_telegram(admin, f"🔴 ظرفیت کشور {country.name} به کمتر از 200 گیگ رسیده.")
                    except:pass




    return HttpResponse("OK")
