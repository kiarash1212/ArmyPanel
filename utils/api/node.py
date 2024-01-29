from utils.api.request import get_request, post_request
from utils.api.urls import NODES_LIST_URL, NODE_URL_URL


def fetch_all_nodes(server):
    return get_request(
        url=f"{server.address}{NODES_LIST_URL.format(1, 50)}",
        data={},
        token=server.token
    )


def get_config_url(server, node, account):
    return post_request(
        url=f"{server.address}{NODE_URL_URL}",
        data={'id': node.provider_id},
        token=account.token
    )
