import logging

import requests as re

from ecobud.config import TINK_BASE_URL, TINK_CLIENT_ID, TINK_CLIENT_SECRET
from ecobud.utils import curl, fmt_response

logger = logging.getLogger(__name__)


def get_tink_client_access_token(scope=None):
    url = TINK_BASE_URL + "/api/v1/oauth/token"
    logger.info(url)
    data = {
        "client_id": TINK_CLIENT_ID,
        "client_secret": TINK_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": scope,
    }
    response = re.post(url=url, data=data)
    logger.debug(f"Sent request {curl(response)}")
    logger.debug(f"Got response {fmt_response(response)}")
    return response.json()["access_token"]


def get_user_authorization_code(username):
    client_access_token = get_tink_client_access_token(scope="authorization:grant")
    url = TINK_BASE_URL + "/api/v1/oauth/authorization-grant/delegate"
    headers = {"Authorization": "Bearer " + client_access_token}
    data = {
        "external_user_id": username,
        "scope": "authorization:read,authorization:grant,credentials:refresh,credentials:read,credentials:write,providers:read,user:read",
        "id_hint": "wthisthis",
        "actor_client_id": "df05e4b379934cd09963197cc855bfe9",
    }
    response = re.post(url=url, data=data, headers=headers)
    logger.debug(f"Sent request {curl(response)}")
    logger.debug(f"Got response {fmt_response(response)}")
    return response.json()["code"]
