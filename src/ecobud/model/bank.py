import random
import string

from ecobud.config import SELF_BASE_URL, TINK_CLIENT_ID
from ecobud.connections.mongo import (
    tink_states_collection,
    users_collection,
)
from ecobud.connections.tink import get_user_authorization_code


class MissingState(Exception):
    pass


def get_random_string(length):
    result_str = "".join(
        random.choice(string.ascii_letters) for _ in range(length)
    )
    return result_str


def handle_callback_bank_connection(credentials_id, state):
    state_record = tink_states_collection.find_one(
        {"state": state, "type": "bank_connection"}
    )

    if state is None:
        raise MissingState("State not found")

    user = state_record["username"]
    tink_states_collection.delete_one(state_record)
    user_record = users_collection.find_one({"username": user})
    user_record["credentials"].append(credentials_id)
    users_collection.replace_one({"username": user}, user_record)
    del user_record["_id"]
    return user_record

