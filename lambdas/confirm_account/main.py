import boto3
import os
import json

REGION = os.getenv('REGION')

cognito_client = boto3.client("cognito-idp", region_name=REGION)
dynamodb_client = boto3.resource("dynamodb", region_name=REGION)

COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")

DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")
users_table = dynamodb_client.Table(DYNAMODB_TABLE)


def handler(event, context):
    body = json.loads(event["body"])
    email = body.get("email")
    confirmation_code = body.get("confirmation_code")
    if not email or not confirmation_code:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Email and confirmation code are required!"}),
        }
    try:

        cognito_client.confirm_sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=email,
            ConfirmationCode=confirmation_code
        )

        users_table.update_item(
            Key={"Email": email},
            UpdateExpression="SET Confirmed = :confirmed",
            ExpressionAttributeValues={":confirmed": True}
        )

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Account successfully confirmed. You can now log in."})
        }

    except cognito_client.exceptions.ExpiredCodeException:
        cognito_client.resend_confirmation_code(
            ClientId=COGNITO_CLIENT_ID,
            Username=email
        )

        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Confirmation code expired. A new code has been sent to your email."
            }),
        }

    except cognito_client.exceptions.CodeMismatchException:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid confirmation code."}),
        }

    except cognito_client.exceptions.UserNotFoundException:
        return {
            "statusCode": 404,
            "body": json.dumps({"message": "User does not exist."}),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)}),
        }
