import os
import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")
table = dynamodb.Table(DYNAMODB_TABLE)


def handler(event, context):
    """Lista usuarios con paginación"""
    limit = int(event.get("queryStringParameters", {}).get("limit", 10))
    last_evaluated_key = event.get("queryStringParameters", {}).get("lastKey", None)

    scan_kwargs = {"Limit": limit}

    if last_evaluated_key:
        scan_kwargs["ExclusiveStartKey"] = json.loads(last_evaluated_key)

    try:
        response = table.scan(**scan_kwargs)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "users": response["Items"],
                "lastKey": json.dumps(response.get("LastEvaluatedKey", {}))
            }),
            "headers": {"Content-Type": "application/json"}
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"}
        }