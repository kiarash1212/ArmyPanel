from requests import get
from datetime import datetime

base_transaction_url = "https://apilist.tronscanapi.com/api/transaction-info"


async def crypto_transaction_validation(tx_id, wallet_address):
    result = {
        'validate': False,
        'tx_id': None,
        'amount': 0,
        'fee': None,
        'from_address': None,
        'to_address': None,
        'date': None,
        'confirm': False,
        'status': "FIELDED",
        'details': ""
    }

    # Send get request for get hash_id information
    response = get(base_transaction_url + f"?hash={tx_id}")

    if response.status_code == 200:
        response_data = response.json()
        if response_data != {'riskTransaction': False}:
            result['tx_id'] = response_data["hash"]
            result['fee'] = response_data["cost"]["fee"]
            contract_data = response_data["contractData"]
            result['from_address'] = contract_data["owner_address"]
            result['to_address'] = contract_data["to_address"]
            result['amount'] = float(contract_data["amount"]) / 10 ** 6
            result['confirm'] = response_data["confirmations"]
            result['status'] = response_data["contractRet"]

            result_datetime = int(response_data["timestamp"])
            result['data'] = datetime.fromtimestamp(result_datetime / 1000)

            if wallet_address == result['to_address']:
                result['validate'] = True
        else:
            result['details'] = 'کد تراکنش درست نمی باشد، لطفا کد خود را بررسی نمایید.'
    else:
        result['details'] = 'مشکل در ارتباط با سرور اصلی، لطفا مجددا تلاش نمایید.'
    return result
