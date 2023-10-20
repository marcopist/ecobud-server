import logging

from flask import Flask, request

from ecobud.model.user import create_user, get_user

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

app = Flask(__name__)
logger = logging.getLogger(__name__)


## Register /user POST endpoint
@app.route("/user", methods=["POST"])
def user_post():
    username = request.json["username"]
    user = create_user(username)
    logger.info(f"Created user {user}")
    return user


## Register /user GET endpoint
@app.route("/user/<string:username>", methods=["GET"])
def user_get(username):
    user = get_user(username)
    return user
