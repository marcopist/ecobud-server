import logging
import sys
import urllib.parse

import cachetools.func
import requests as re

from ecobud.config import (
    SELF_BASE_URL,
    TINK_BASE_URL,
    TINK_CLIENT_ID,
    TINK_CLIENT_SECRET,
)
from ecobud.utils import curl, fmt_response

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@cachetools.func.ttl_cache(maxsize=128, ttl=10 * 60)
def get_client_token(scope, grant_type="client_credentials"):
    url = TINK_BASE_URL + "/api/v1/oauth/token"
    data = {
        "client_id": TINK_CLIENT_ID,
        "client_secret": TINK_CLIENT_SECRET,
        "grant_type": grant_type,
        "scope": scope,
    }
    response = re.post(url=url, data=data)
    logger.debug(f"Sent request {curl(response)}")
    logger.debug(f"Got response {fmt_response(response)}")
    return response.json()["access_token"]


@cachetools.func.ttl_cache(maxsize=128, ttl=10 * 60)
def get_user_authorization_code(
    username, scope, delegate=False, **kwargs
):
    client_token = get_client_token(
        scope="authorization:grant",
        grant_type="client_credentials",
    )
    url = TINK_BASE_URL + "/api/v1/oauth/authorization-grant"

    if delegate:
        url += "/delegate"

    headers = {"Authorization": "Bearer " + client_token}
    data = {
        **{
            "external_user_id": username,
            "scope": scope,
        },
        **kwargs,
    }
    response = re.post(url=url, data=data, headers=headers)
    logger.debug(f"Sent request {curl(response)}")
    logger.debug(f"Got response {fmt_response(response)}")
    return response.json()["code"]


@cachetools.func.ttl_cache(maxsize=128, ttl=10 * 60)
def get_user_token(username, scope):
    user_authorization_code = get_user_authorization_code(
        username, scope
    )
    url = TINK_BASE_URL + "/api/v1/oauth/token"
    data = {
        "client_id": TINK_CLIENT_ID,
        "client_secret": TINK_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": user_authorization_code,
    }
    response = re.post(url=url, data=data)
    logger.debug(f"Sent request {curl(response)}")
    logger.debug(f"Got response {fmt_response(response)}")
    return response.json()["access_token"]


def create_user(username):
    client_token = get_client_token("user:create")
    url = TINK_BASE_URL + "/api/v1/user/create"
    headers = {
        "Authorization": "Bearer " + client_token,
        "Content-Type": "application/json",
    }
    data = {
        "external_user_id": username,
        "market": "GB",
        "locale": "en_US",
        "retention_class": "permanent",
    }
    response = re.post(url=url, json=data, headers=headers)
    return response.json()


def get_user(username):
    user_token = get_user_token(username, "user:read")
    url = TINK_BASE_URL + "/api/v1/user"
    headers = {"Authorization": "Bearer " + user_token}
    response = re.get(url=url, headers=headers)
    logger.debug(f"Sent request {curl(response)}")
    logger.debug(f"Got response {fmt_response(response)}")
    return response.json()


def delete_user(username):
    user_token = get_user_token(username, "user:delete")
    url = TINK_BASE_URL + "/api/v1/user/delete"
    headers = {"Authorization": "Bearer " + user_token}
    response = re.post(url=url, headers=headers)
    logger.debug(f"Sent request {curl(response)}")
    logger.debug(f"Got response {fmt_response(response)}")
    return response.json()


def get_user_transactions(username, noPages=1):
    user_token = get_user_token(username, "transactions:read")
    url = TINK_BASE_URL + "/data/v2/transactions"
    headers = {"Authorization": "Bearer " + user_token}

    page = 0
    transactions = []
    next_page_token = None

    while page < noPages:
        page += 1
        params = (
            {"pageToken": next_page_token} if next_page_token else {}
        )
        response = re.get(url=url, headers=headers, params=params)
        data = response.json()
        logger.debug(f"Sent request {curl(response)}")
        logger.debug(f"Got response {fmt_response(response)}")
        transactions.extend(data["transactions"])
        next_page_token = data["nextPageToken"]

    return transactions


def get_bank_connection_url(username):
    user_authorization_code = get_user_authorization_code(
        username,
        scope=(
            "authorization:read,"
            "authorization:grant,"
            "credentials:refresh,"
            "credentials:read,"
            "credentials:write,"
            "providers:read,"
            "user:read"
        ),
        delegate=True,
        actor_client_id="df05e4b379934cd09963197cc855bfe9",
        id_hint="hint",
    )
    redirect_to = SELF_BASE_URL + "/bank/callback"
    encoded_redirect_to = urllib.parse.quote_plus(redirect_to)
    bank_connection_url = (
        f"https://link.tink.com/1.0/transactions/connect-accounts"
        f"?client_id={TINK_CLIENT_ID}"
        f"&redirect_uri={encoded_redirect_to}"
        f"&authorization_code={user_authorization_code}"
        "&market=GB"
        "&locale=en_US"
    )

    return bank_connection_url


def register_transaction_webhook(webhook_url=None):
    client_token = get_client_token("webhook-endpoints")
    url = TINK_BASE_URL + "/events/v2/webhook-endpoints"
    if not webhook_url:
        webhook_url = SELF_BASE_URL + "/tink/webhook"
    headers = {
        "Authorization": "Bearer " + client_token,
        "Content-Type": "application/json",
    }
    data = {
        "description": "webhook",
        "disabled": False,
        "enabledEvents": ["account-transactions:modified"],
        "url": webhook_url,
    }
    response = re.post(url=url, json=data, headers=headers)
    logger.debug(f"Sent request {curl(response)}")
    logger.debug(f"Got response {fmt_response(response)}")
    return response.json()
