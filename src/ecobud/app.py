from flask import Flask, request

app = Flask(__name__)

@app.route("/hello", methods=["POST"])
def hello():
    return request.json