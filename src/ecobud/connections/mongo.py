from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from ecobud.config import MONGO_CONNECTION_STRING, MONGO_DB_NAME

client = MongoClient(
    MONGO_CONNECTION_STRING,
    server_api=ServerApi("1"),
)

collections = client[MONGO_DB_NAME]
