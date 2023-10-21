import logging

from flask import Flask, request, session

from ecobud.connections.tink import get_bank_connection_url

# from ecobud.model.bank import (
#     get_bank_connection_url,
#     handle_callback_bank_connection,
# )
from ecobud.model.user import (
    UserAlreadyExists,
    UserNotFound,
    WrongPassword,
    create_user,
    login_user,
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
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


@app.route("/login", methods=["POST"])
def login_post():
    username = request.json["username"]
    password = request.json["password"]
    try:
        login_user(username, password)
        session["username"] = username
    except UserNotFound:
        return {"error": "User not found"}, 404
    except WrongPassword:
        return {"error": "Wrong password"}, 401


@app.route("/bank/link", methods=["GET"])
def bank_post():
    username = session.get("username")
    if not username:
        return {"error": "Not logged in"}, 401
    bank_connection_url = get_bank_connection_url(username)
    return {"url": bank_connection_url}


@app.route("/bank/callback", methods=["GET"])
def bank_callback_get():
    username = session.get("username")
    if not username:
        return {"error": "Not logged in"}, 401
    code = request.args.get("code")
    return {"success": True}
