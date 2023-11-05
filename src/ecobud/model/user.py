import logging

import bcrypt

from ecobud.connections import tink
from ecobud.connections.mongo import collections
from ecobud.utils import JSONDict, JSONList, JSONType

logger = logging.getLogger(__name__)

usersdb = collections["users"]


class UserAlreadyExists(Exception):
    pass


class TinkUserAlreadyExists(Exception):
    pass


class UserNotFound(Exception):
    pass


class WrongPassword(Exception):
    pass


def create_user(username: str, email: str, password: str) -> bool:
    logger.debug(f"Creating user {username}")
    try:
        user = _get_user(username)
        raise UserAlreadyExists(f"User {username} already exists")
    except UserNotFound:
        pass

    try:
        tink_user_id = tink.create_user(username)
    except TinkUserAlreadyExists:
        logger.debug(f"User {username} already exists in Tink")
        tink_user_id = tink.get_user(username)["id"]

    salt = bcrypt.gensalt()
    encrypted_password = bcrypt.hashpw(
        password.encode("utf-8"),
        salt,
    ).decode("utf-8")

    user = {
        "username": username,
        "email": email,
        "password": encrypted_password,
        "tink_user_id": tink_user_id,
        "credentials": [],
    }

    logger.debug(f"Saving user {username}")
    usersdb.insert_one(user)
    logger.debug(f"User {username} created")
    return True


def login_user(username: str, password: str) -> bool:
    logger.debug(f"Logging in user {username}")
    user = _get_user(username)

    decoded_encrypted_password: str = user["password"]  # type: ignore
    encrypted_password = decoded_encrypted_password.encode("utf-8")

    if not bcrypt.checkpw(password.encode("utf-8"), encrypted_password):
        logger.debug(f"Wrong password for user {username}")
        raise WrongPassword(f"Wrong password for user {username}")
    return True


def _get_user(username: str) -> JSONDict:
    logger.debug(f"Getting user {username}")
    user = usersdb.find_one({"username": username})
    if user is None:
        raise UserNotFound(f"User {username} not found")
    return user


if __name__ == "__main__":
    print(create_user("test0", email="test0@test.com", password="test0"))
