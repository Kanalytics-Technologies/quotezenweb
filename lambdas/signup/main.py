import boto3
import os
import json
import uuid

REGION = os.getenv('REGION')

cognito_client = boto3.client("cognito-idp", region_name=REGION)
dynamodb_client = boto3.resource("dynamodb", region_name=REGION)

DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")

COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")

users_table = dynamodb_client.Table(DYNAMODB_TABLE)


def handler(event, context):
    try:
        body = json.loads(event["body"])
        email = body.get("email")
        fullname = body.get("fullname")
        password = body.get("password")
        role = body.get("role")  # carrier, shipper, admin
        company = body.get("company")

        if not email or not password or not role or not company:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "More fields required!"}),
            }

        response = cognito_client.sign_up(
            ClientId=os.getenv("COGNITO_CLIENT_ID"),
            Username=email,
            Password=password,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "name", "Value": fullname}
            ],
        )

        users_table.put_item(
            Item={
                "user_id": str(uuid.uuid4()),  # ID único
                "Email": email,
                "Role": role,
                "Company": company,
                "Confirmed": False,
                "Fullname": fullname
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "User created. Check your email to confirm your account."}
            ),
        }

    except cognito_client.exceptions.UsernameExistsException:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "User already exists."}),
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"message": str(e)})}