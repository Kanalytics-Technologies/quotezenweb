import json
import boto3
import uuid
import os

cognito = boto3.client("cognito-idp")
dynamodb = boto3.resource("dynamodb")
ses = boto3.client("ses")

USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")
SES_SENDER_EMAIL = "noreply@yourdomain.com"  # 📩 Reemplaza con un correo verificado en SES

table = dynamodb.Table(DYNAMODB_TABLE)


def handler(event, context):
    """Crea un usuario en Cognito y envía un correo de confirmación manual."""
    try:
        body = json.loads(event["body"])
        email = body["email"]
        fullname = body["fullname"]
        company = body["company"]
        role = body["role"]

        # 1️⃣ 🔹 Crear usuario en Cognito (sin confirmarlo)
        response = cognito.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=email,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "false"},
            ],
            TemporaryPassword=str(uuid.uuid4())[:8],  # 📌 Contraseña temporal aleatoria
            MessageAction="SUPPRESS"  # 🔹 Evita que Cognito envíe el email de confirmación
        )

        # 2️⃣ 🔹 Generar token de confirmación único
        invite_token = str(uuid.uuid4())

        # 3️⃣ 🔹 Guardar en DynamoDB
        table.put_item(
            Item={
                "Email": email,
                "Company": company,
                "Fullname": fullname,
                "Role": role,
                "Confirmed": False,
                "InviteToken": invite_token
            }
        )

        # 4️⃣ 🔹 Enviar email manualmente con SES
        confirmation_link = f"https://yourfrontend.com/confirm?email={email}&token={invite_token}"
        ses.send_email(
            Source=SES_SENDER_EMAIL,
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": "Welcome to Quotezen - Confirm Your Account"},
                "Body": {
                    "Text": {"Data": f"Click here to confirm your account and set your password: {confirmation_link}"}
                },
            },
        )

        return {"statusCode": 201,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization"
                },
                "body": json.dumps({"message": "User created. Confirmation email sent."})}

    except Exception as e:
        return {"statusCode": 500,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization"
                },
                "body": json.dumps({"error": str(e)})}