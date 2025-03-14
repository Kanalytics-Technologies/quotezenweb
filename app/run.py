from flask import Flask, render_template
import boto3
import os

app = Flask(__name__)

# 🔹 Configuración de AWS DynamoDB
dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION"))
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")
users_table = dynamodb.Table(DYNAMODB_TABLE)

@app.route("/users")
def users():
    response = users_table.scan()
    users = response.get("Items", [])
    return render_template('users.html', users=users)


if __name__ == "__main__":
    app.run(debug=True)