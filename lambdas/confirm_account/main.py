import json
import boto3
import os

cognito = boto3.client("cognito-idp")
dynamodb = boto3.resource("dynamodb")

USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")

table = dynamodb.Table(DYNAMODB_TABLE)


def handler(event, context):
    """Confirma la cuenta y permite establecer una nueva contraseña."""
    try:
        body = json.loads(event["body"])
        email = body["email"]
        invite_token = body["token"]
        new_password = body["new_password"]

        # 1️⃣ 🔹 Buscar usuario en DynamoDB
        response = table.get_item(Key={"Email": email})
        user = response.get("Item")

        if not user or user.get("InviteToken") != invite_token:
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid token"})}

        # 2️⃣ 🔹 Establecer nueva contraseña en Cognito
        cognito.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=email,
            Password=new_password,
            Permanent=True  # 🔹 Permite el inicio de sesión inmediato sin cambiar contraseña
        )

        # 3️⃣ 🔹 Marcar como confirmado en DynamoDB
        table.update_item(
            Key={"Email": email},
            UpdateExpression="SET Confirmed = :val REMOVE InviteToken",
            ExpressionAttributeValues={":val": True}
        )

        return {"statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization"
                },
                "body": json.dumps({"message": "Account confirmed successfully."})}

    except Exception as e:
        return {"statusCode": 500,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization"
                },
                "body": json.dumps({"error": str(e)})}