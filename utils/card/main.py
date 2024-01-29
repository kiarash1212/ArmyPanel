import re

from persiantools.jdatetime import JalaliDateTime


def get_data_sms(message):
    date_pattern = r'(\d{2}/\d{2}/\d{2}_\d{2}:\d{2})'
    amount_pattern = r'مبلغ: ([\d,]+) ريال'

    if 'واریز' not in message:
        return None, None

    date_match = re.search(date_pattern, message)
    if date_match:
        date = date_match.group(1)
        date, time = date.split("_")

        year, month, day = date.split("/")
        hour, minute = time.split(":")

        jalali_date = JalaliDateTime(int(f"14{year}"), int(month), int(day), int(hour), int(minute))
        date = jalali_date.to_gregorian()
    else:
        date = None

    amount_match = re.search(amount_pattern, message)
    if amount_match:
        amount = amount_match.group(1)
    else:
        amount = None

    if amount and date:
        return int(amount.replace(",", "")), date
    return None, None
