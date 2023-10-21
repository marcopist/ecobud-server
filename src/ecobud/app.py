import logging

from flask import Flask, request

from ecobud.model.bank import get_bank_connection_url, handle_callback_bank_connection
from ecobud.model.user import create_user, get_user, UserAlreadyExists


logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = Flask(__name__)
logger = logging.getLogger(__name__)


@app.route("/user", methods=["POST"])
def user_post():
    username = request.json["username"]
    email = request.json["email"]
    password = request.json["password"]
    try:
        create_user(username, email, password)
    except UserAlreadyExists:
        return {"error": "User already exists"}, 409
    
    return {"username": username}, 201


@app.route("/user/<string:username>", methods=["GET"])
def user_get(username):
    user = get_user(username)
    return user


@app.route("/user/<string:username>/bank/link", methods=["GET"])
def bank_post(username):
    bank_connection_url = get_bank_connection_url(username)
    return {"url": bank_connection_url}
