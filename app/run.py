from flask import Flask, render_template
# import boto3
# import os

app = Flask(__name__)


@app.route("/users")
def users():
    return "hola"


if __name__ == "__main__":
    app.run(debug=True)
