import logging

from flask import Flask, request, session

from ecobud.config import FLASK_SECRET_KEY
from ecobud.connections.tink import get_bank_connection_url, get_user_transactions
from ecobud.model.analytics import get_analytics
from ecobud.model.transactions import (
    get_specific_transaction,
    get_transactions,
    update_transaction,
)
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

app.secret_key = FLASK_SECRET_KEY


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

    return {"username": username}, 200


@app.route("/bank/link", methods=["GET"])
def bank_post():
    username = session.get("username")
    if not username:
        return {"error": "Not logged in"}, 401
    bank_connection_url = get_bank_connection_url(username)
    return {"url": bank_connection_url}


@app.route("/tink/transactions", methods=["GET"])
def tranasctions_get():
    username = session.get("username")
    if not username:
        return {"error": "Not logged in"}, 401
    transactions = get_user_transactions(username)
    return {"transactions": transactions}


@app.route("/tink/webhook", methods=["POST"])
def webhook_post():
    logger.debug(f"Got webhook {request.json}")
    return {"success": True}


@app.route("/transactions", methods=["GET"])
def transactions_get():
    logger.debug(f"Getting transactions for {session.get('username')}")
    username = session.get("username")
    if not username:
        return {"error": "Not logged in"}, 401
    transactions = get_transactions(username)
    logger.debug(f"Got transactions for {session.get('username')}, number is {len(transactions)}")
    return {"transactions": transactions}, 200


@app.route("/transactions/<transaction_id>", methods=["GET"])
def transaction_get(transaction_id):
    username = session.get("username")
    if not username:
        return {"error": "Not logged in"}, 401
    transaction = get_specific_transaction(username, transaction_id)
    return {"transaction": transaction}, 200


@app.route("/transactions/<transaction_id>", methods=["PUT"])
def transaction_put(transaction_id):
    logger.debug(f"Got update request for transaction {transaction_id}")
    transaction = request.json["transaction"]
    logger.debug(f"Updating transaction {transaction_id} with {transaction}")
    username = session.get("username")
    if not username:
        logger.debug(f"Not logged in")
        return {"error": "Not logged in"}, 401
    if username != transaction["username"]:
        logger.debug(f"Wrong username")
        return {"error": "Wrong username"}, 401

    if transaction_id != transaction["_id"]:
        logger.debug(f"Wrong transaction id")
        return {"error": "Wrong transaction id"}, 401

    update_transaction(transaction)
    logger.debug(f"[Success] Updated transaction {transaction_id}")
    return {"success": True}, 200


@app.route("/analytics/<start_date>/<end_date>", methods=["GET"])
def analytics_get(start_date, end_date):
    username = session.get("username")
    logger.debug(f"Got request for analytics for user {username} between {start_date} and {end_date}")
    if not username:
        return {"error": "Not logged in"}, 401

    analytics = get_analytics(start_date, end_date, username)
    logger.debug(f"Got analytics {analytics}")
    return {"analytics": analytics}, 200


@app.route("/logout", methods=["POST"])
def logout_post():
    logger.debug(f"Logging out {session.get('username')}")
    session.pop("username", None)
    return {"success": True}, 200
