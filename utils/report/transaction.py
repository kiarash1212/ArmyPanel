from datetime import timedelta, datetime

from django.db.models import Sum, Q
from django.utils import timezone
from persiantools.jdatetime import JalaliDate

from models.transactions.models import Transaction


def get_transaction_report(data):
    start_date = data.request.GET.get("start_date")
    end_date = data.request.GET.get("end_date")

    today = datetime.now()
    start_of_month = today.replace(day=1)
    end_of_month = today.replace(day=29)

    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    print(start_of_month, end_of_month)
    income_this_month = Transaction.objects.filter(
        Q(type="order") | Q(type="wallet") | Q(type="crypto") | Q(type="card"),
        status="payed",
        published__range=(end_of_month, start_of_month)
    ).aggregate(Sum("amount"))

    income_today = Transaction.objects.filter(
        Q(type="order") | Q(type="wallet") | Q(type="crypto") | Q(type="card"),
        status="payed",
        published=today
    ).aggregate(Sum("amount"))

    income_this_week = Transaction.objects.filter(
        Q(type="order") | Q(type="wallet") | Q(type="crypto") | Q(type="card"),
        status="payed",
        published__range=(start_of_week, end_of_week)
    ).aggregate(Sum("amount"))

    total_income_month = income_this_month["amount__sum"] or 0
    total_income_today = income_today["amount__sum"] or 0
    total_income_week = income_this_week["amount__sum"] or 0

    cost_this_month = Transaction.objects.filter(
        type="cost",
        status="payed",
        published__range=(start_of_month, end_of_month)
    ).aggregate(Sum("amount"))

    cost_today = Transaction.objects.filter(
        type="cost",
        status="payed",
        published=today
    ).aggregate(Sum("amount"))

    cost_this_week = Transaction.objects.filter(
        type="cost",
        status="payed",
        published__range=(start_of_week, end_of_week)
    ).aggregate(Sum("amount"))

    profit_this_month = total_income_month - (cost_this_month["amount__sum"] or 0)
    profit_today = total_income_today - (cost_today["amount__sum"] or 0)
    profit_this_week = total_income_week - (cost_this_week["amount__sum"] or 0)

    daily_data = {
        'total': total_income_today,
        'cost': cost_today['amount__sum'] or 0,
        'profit': profit_today
    }

    weekly_data = {
        'total': total_income_week,
        'cost': cost_this_week['amount__sum'] or 0,
        'profit': profit_this_week
    }

    monthly_data = {
        'total': total_income_month,
        'cost': cost_this_month['amount__sum'] or 0,
        'profit': profit_this_month
    }
    income_in_time_range = {'total': 0, 'cost': 0, 'profit': 0}

    if start_date and end_date:
        day, month, year = start_date.split("/")
        start_date_jalali = JalaliDate(int(year), int(month), int(day)).to_gregorian()

        print(start_date_jalali, type(start_date_jalali))
        day, month, year = end_date.split("/")
        end_date_jalali = JalaliDate(int(year), int(month), int(day)).to_gregorian()


        income = Transaction.objects.filter(
            Q(type="order") | Q(type="wallet") | Q(type="crypto") | Q(type="card"),
            status="payed",
            published__range=(start_date_jalali, end_date_jalali)
        ).aggregate(Sum("amount"))

        cost = Transaction.objects.filter(
            type="cost",
            status="payed",
            published__range=(start_date_jalali, end_date_jalali)
        ).aggregate(Sum("amount"))

        profit = (income["amount__sum"] or 0) - (cost["amount__sum"] or 0)

        income_in_time_range = {
            'total': income['amount__sum'] or 0,
            'cost': cost['amount__sum'] or 0,
            'profit': profit
        }
    print(daily_data)
    return daily_data, weekly_data, monthly_data, income_in_time_range

def get_today_transactions():
    today = datetime.now()
    income_today = Transaction.objects.filter(
        Q(type="order") | Q(type="wallet") | Q(type="crypto") | Q(type="card"),
        status="payed",
        published__day=today.day,
        published__month=today.month,
        published__year=today.year
    ).all()

    print(income_today)
    return income_today

def get_month_transactions():
    today = datetime.now()
    income_month = Transaction.objects.filter(
        Q(type="order") | Q(type="wallet") | Q(type="crypto") | Q(type="card"),
        status="payed",
        published__month=today.month,
        published__year=today.year
    ).all()

    return income_month