from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from ecobud.config import MONGO_CONNECTION_STRING, MONGO_DB_NAME

client = MongoClient(
    MONGO_CONNECTION_STRING,
    server_api=ServerApi("1"),
)

collections = client[MONGO_DB_NAME]


def test_connection():  # pragma: no cover
    return collections.list_collection_names()


def get_size():  # pragma: no cover
    return collections.command("dbstats")["dataSize"] * 1e-6


if __name__ == "__main__":
    print("Collections are", test_connection())
    print("Size total is: ", get_size(), "MB")
