from utils.api.request import post_request, get_request
from utils.api.urls import CREATE_ACCOUNT_URL, INFORMATION_ACCOUNT_URL, SEARCH_ACCOUNT_URL, DELETE_ACCOUNT_URL


def create_account(server, data):
    return post_request(
        url=f"{server.address}{CREATE_ACCOUNT_URL}",
        data={
            "quota": data['value'],
            "download": 0,
            "upload": 0,
            "username": data['username'],
            "pass": data['password'],
            "roleId": 3,
            "deleted": 0,
            "expireTime": data['expireTime'],
        },
        token=server.token
    )


def information_account(server, account_id):
    return get_request(
        url=f"{server.address}{INFORMATION_ACCOUNT_URL}",
        data={
            "id": account_id
        },
        token=server.token
    )


def delete_account(server, account_id):
    return post_request(
        url=f"{server.address}{DELETE_ACCOUNT_URL}",
        data={
            "id": account_id
        },
        token=server.token
    )


def search_account(server, account_id):
    return get_request(
        url=f"{server.address}{SEARCH_ACCOUNT_URL}?pageNum=1&pageSize=10&username={account_id}",
        token=server.token
    )
