from utils.api.request import post_request, get_request
from utils.api.urls import LOGIN_URL, ACCOUNT_INFO_URL


def get_new_token(server, account=None):
    if account:
        data = {
            'username': account.username,
            'pass': account.password
        }
    else:
        data = {
            'username': server.username,
            'pass': server.password
        }

    data['captchaId'] = ""
    data['captchaCode'] = ""
    return post_request(
        url=f"{server.address}{LOGIN_URL}",
        data=data,

    )


def check_token_status(server, account=None):
    if account:
        token = account.token
    else:
        token = server.token
    return get_request(
        url=f"{server.address}{ACCOUNT_INFO_URL}",
        data={},
        token=token
    )
