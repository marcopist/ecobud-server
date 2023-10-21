import logging

import bcrypt
import requests as re

from ecobud.config import SELF_BASE_URL
from ecobud.connections.mongo import users_collection
from ecobud.connections.tink import TINK_BASE_URL, TINK_CLIENT_ID, get_tink_client_access_token
from ecobud.utils import curl, fmt_response

logger = logging.getLogger(__name__)


class UserAlreadyExists(Exception):
    pass

class TinkUserAlreadyExists(Exception):
    pass

class UserNotFound(Exception):
    pass


def _register_user_with_tink(username):
    logger.debug(f"Registering user {username} with Tink")

    tink_client_access_token = get_tink_client_access_token(scope="user:create")
    url = TINK_BASE_URL + "/api/v1/user/create"
    headers = {
        "Authorization": "Bearer " + tink_client_access_token,
        "Content-Type": "application/json",
    }
    data = {"external_user_id": username, "market": "GB", "locale": "en_US"}
    response = re.post(url=url, json=data, headers=headers)

    logger.debug(f"Sent request {curl(response)}")
    logger.debug(f"Got response {fmt_response(response)}")

    response_data = response.json()

    if response.status_code > 299:
        if response_data["errorCode"] == "user.user_with_external_user_id_already_exists":
            raise TinkUserAlreadyExists()

    tink_user_id = response_data["user_id"]

    return tink_user_id

def _get_tink_user_id(username):
    tink_client_access_token = get_tink_client_access_token(scope="user:read")
    url = TINK_BASE_URL + "/api/v1/user"
    headers = {
        "Authorization": "Bearer " + tink_client_access_token
    }
    response = re.get(url=url, headers=headers)
    logger.debug(f"Sent request {curl(response)}")
    logger.debug(f"Got response {fmt_response(response)}")
    response_data = response.json()
    tink_user_id = response_data["id"]
    return tink_user_id


def create_user(username, email, password):
    logger.debug(f"Creating user {username}")
    user = get_user(username)

    if user is not None:
        logger.debug(f"User {username} already exists")
        raise UserAlreadyExists(f"User {username} already exists")

    try:
        tink_user_id = _register_user_with_tink(username)
    except TinkUserAlreadyExists:
        logger.debug(f"User {username} already exists in Tink")
        tink_user_id = _get_tink_user_id(username)
        pass

    salt = bcrypt.gensalt()
    encrypted_password = bcrypt.hashpw(password, salt).decode("utf-8")

    user = {
        "username": username,
        "email": email,
        "password": encrypted_password,
        "tink_user_id": tink_user_id,
        "credentials": [],
    }

    logger.debug(f"Saving user {username}")
    users_collection.insert_one(user)
    del user["_id"]
    logger.debug(f"User {username} created")
    return True


def get_user(username):
    logger.debug(f"Getting user {username}")
    user = users_collection.find_one({"username": username})
    if user is None:
        raise UserNotFound(f"User {username} not found")
    return user
