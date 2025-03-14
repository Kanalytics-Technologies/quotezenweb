import boto3
import os
import json

REGION = os.getenv("REGION")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")

cognito_client = boto3.client("cognito-idp", region_name=REGION)
dynamodb_client = boto3.resource("dynamodb", region_name=REGION)
users_table = dynamodb_client.Table(DYNAMODB_TABLE)


def handler(event, context):
    try:
        body = json.loads(event["body"])
        email = body.get("email")
        password = body.get("password")

        if not email or not password:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization"
                },
                "body": json.dumps({"message": "Email and password are required"})}

        response = cognito_client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": email, "PASSWORD": password},
        )

        id_token = response["AuthenticationResult"]["IdToken"]
        access_token = response["AuthenticationResult"]["AccessToken"]
        refresh_token = response["AuthenticationResult"]["RefreshToken"]

        user_data = users_table.get_item(Key={"Email": email})

        if "Item" not in user_data:
            return {
                "statusCode": 404,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization"
                },
                "body": json.dumps({"message": "User not found in database"})}

        user_info = user_data["Item"]

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            },
            "body": json.dumps({
                "message": "Login successful",
                "id_token": id_token,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "email": user_info["Email"],
                    "role": user_info["Role"],
                    "company": user_info["Company"],
                    "fullname": user_info.get("Fullname", ""),
                    "profile_picture_url": user_info.get("profile_picture_url", "")
                }
            }),
        }

    except cognito_client.exceptions.NotAuthorizedException:
        return {
            "statusCode": 401,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            },
            "body": json.dumps({"message": "Invalid credentials"})}

    except cognito_client.exceptions.UserNotFoundException:
        return {
            "statusCode": 404,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            },
            "body": json.dumps({"message": "User does not exist"})}

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            },
            "body": json.dumps({"message": str(e)})}