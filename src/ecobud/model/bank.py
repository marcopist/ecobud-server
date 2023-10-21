import random
import string

from ecobud.config import SELF_BASE_URL, TINK_CLIENT_ID
from ecobud.connections.mongo import tink_states_collection, users_collection
from ecobud.connections.tink import get_user_authorization_code


class MissingState(Exception):
    pass


def get_random_string(length):
    result_str = "".join(random.choice(string.ascii_letters) for _ in range(length))
    return result_str


def get_bank_connection_url(username):
    user_authorization_code = get_user_authorization_code(username)
    redirect_to = f"{SELF_BASE_URL}/callback"
    state = get_random_string(10)
    tink_states_collection.insert_one(
        {"state": state, "username": username, "type": "bank_connection"}
    )
    bank_connection_url = (
        f"https://link.tink.com/1.0/transactions/connect-accounts"
        f"?client_id={TINK_CLIENT_ID}"
        f"&state={state}"
        f"&redirect_uri={redirect_to}"
        f"&authorization_code={user_authorization_code}"
        "&market=GB"
        "&locale=en_US"
    )

    return bank_connection_url


def handle_callback_bank_connection(credentials_id, state):
    state_record = tink_states_collection.find_one({"state": state, "type": "bank_connection"})

    if state is None:
        raise MissingState("State not found")

    user = state_record["username"]
    tink_states_collection.delete_one(state_record)
    user_record = users_collection.find_one({"username": user})
    user_record["credentials"].append(credentials_id)
    users_collection.replace_one({"username": user}, user_record)
    del user_record["_id"]
    return user_record


if __name__ == "__main__":
    print(get_bank_connection_url("test2"))
