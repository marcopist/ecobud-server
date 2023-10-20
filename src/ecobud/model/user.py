import logging

import requests as re

from ecobud.config import SELF_BASE_URL
from ecobud.connections.mongo import users_collection
from ecobud.connections.tink import TINK_BASE_URL, TINK_CLIENT_ID, get_tink_client_access_token, get_user_authorization_code
from ecobud.utils import curl, fmt_response

logger = logging.getLogger(__name__)


class UserAlreadyExists(Exception):
    pass


class UserNotFound(Exception):
    pass


def _register_user_with_tink(username):
    logger.debug(f"Registering user {username} with Tink")

    tink_client_access_token = get_tink_client_access_token(scope="user:create")
    url = TINK_BASE_URL + "/api/v1/user/create"
    headers = {"Authorization": "Bearer " + tink_client_access_token, "Content-Type": "application/json"}
    data = {"external_user_id": username, "market": "GB", "locale": "en_US"}
    response = re.post(url=url, json=data, headers=headers)

    logger.debug(f"Sent request {curl(response)}")
    logger.debug(f"Got response {fmt_response(response)}")

    response_data = response.json()

    if response.status_code > 299:
        if response_data["errorCode"] == "user.user_with_external_user_id_already_exists":
            raise UserAlreadyExists()

    tink_user_id = response_data["user_id"]

    return tink_user_id


def create_user(username):
    logger.debug(f"Creating user {username}")
    try:
        tink_user_id = _register_user_with_tink(username)
    except UserAlreadyExists:
        logger.debug(f"User {username} already exists")
        tink_user_id = get_user(username)["tink_user_id"]
        return {"username": username, "tink_user_id": tink_user_id}
    user = {"username": username, "tink_user_id": tink_user_id}
    logger.debug(f"Saving user {user}")
    users_collection.insert_one(user)
    del user["_id"]
    logger.debug(f"User {username} created")
    return user


def get_user(username):
    logger.debug(f"Getting user {username}")
    user = users_collection.find_one({"username": username})
    if user is None:
        raise UserNotFound(f"User {username} not found")
    return user


def get_bank_connection_url(username):
    user_authorization_code = get_user_authorization_code(username)
    redirect_to = f"{SELF_BASE_URL}/callback"
    bank_connection_url = (
        f"https://link.tink.com/1.0/transactions/connect-accounts"
        f"?client_id={TINK_CLIENT_ID}"
        f"&redirect_uri={redirect_to}"
        f"&authorization_code={user_authorization_code}"
        "&market=GB"
        "&locale=en_US"
    )

    return bank_connection_url
