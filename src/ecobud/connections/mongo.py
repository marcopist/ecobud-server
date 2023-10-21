from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from ecobud.config import MONGO_CONNECTION_STRING

client = MongoClient(MONGO_CONNECTION_STRING, server_api=ServerApi("1"))

users_collection = client["ecobud-dev"]["users"]
tink_states_collection = client["ecobud-dev"]["tink_states"]
