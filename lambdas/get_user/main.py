import json
import os
import boto3

cognito_client = boto3.client("cognito-idp", region_name=os.getenv("AWS_REGION"))
dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION"))

USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
USERS_TABLE = os.getenv("DYNAMODB_TABLE")

users_table = dynamodb.Table(USERS_TABLE)


def create_response(status_code, message):
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        },
        "body": json.dumps({"message": message}) if isinstance(message, str) else json.dumps({"user": message}),
    }


def handler(event, context):
    auth_header = event.get("headers", {}).get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return create_response(401, "Missing or invalid token")

    token = auth_header.split(" ")[1]

    try:
        response = cognito_client.get_user(AccessToken=token)
        cognito_attributes = {attr["Name"]: attr["Value"] for attr in response["UserAttributes"]}

        user_email = cognito_attributes.get("email")
        fullname = cognito_attributes.get("name")
    except Exception as e:
        return create_response(500, f"Error fetching Cognito user: {str(e)}")

    try:
        dynamo_response = users_table.get_item(Key={"Email": user_email})
        user_data = dynamo_response.get("Item", {})

        user_info = {
            "email": user_email,
            "fullname": fullname,
            "role": user_data.get("Role", "unknown"),
            "company": user_data.get("Company", "unknown"),
            "confirmed": user_data.get("Confirmed", False),
        }

        return create_response(200, user_info)
    except Exception as e:
        return create_response(500, f"Error fetching user data: {str(e)}")