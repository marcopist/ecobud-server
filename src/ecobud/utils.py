import curlify


def curl(response):
    return curlify.to_curl(response.request)


def fmt_response(response):
    if response.status_code == 200:
        return response.json()
    else:
        return f"<{response.status_code}>: {response.text}"
