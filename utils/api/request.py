import json
import requests


def post_request(url, data, token=None):
    payload = json.dumps(data)
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json'
    }
    if token: headers.update({
        'Authorization': f'Bearer {token}',
        'Cookie': f'Authorization=Bearer%20{token}'
    })
    response = requests.request("POST", url, headers=headers, data=payload, verify=False, timeout=10)
    return json.loads(response.text)


def get_request(url, data=None, token=None):
    headers = {
        'Accept': 'application/json, text/plain, */*',
    }
    if token:
        headers.update({
            'Authorization': f'Bearer {token}',
            'Cookie': f'Authorization=Bearer%20{token}'
        })

    response = requests.get(
        url,
        params=data,
        headers=headers,
        verify=False,
        timeout=15,
    )
    return json.loads(response.text)
