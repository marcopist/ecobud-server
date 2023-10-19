from flask import Flask
from flask import request


app = Flask(__name__)

@app.route("/wehbooks/tink/transactions", methods=["POST"])
def webhook_tink_transaction():
    data = request.form
    return data

