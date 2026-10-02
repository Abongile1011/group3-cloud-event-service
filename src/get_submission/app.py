import json
import logging
import os

import boto3
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get("SUBMISSIONS_TABLE", "StudentSubmissions")
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT")

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=DYNAMODB_ENDPOINT if DYNAMODB_ENDPOINT else None,
)

table = dynamodb.Table(TABLE_NAME)


def json_default(value):
    if isinstance(value, Decimal):
        if value % 1 == 0:
            return int(value)
        return float(value)

    raise TypeError(
        f"Object of type {type(value).__name__} is not JSON serializable"
    )


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, default=json_default),
    }


def lambda_handler(event, context):
    request_id = getattr(context, "aws_request_id", "unknown")

    logger.info(
        json.dumps({
            "event": "get_submission_received",
            "request_id": request_id,
        })
    )

    # Get submission_id from API Gateway path
    path_parameters = event.get("pathParameters") or {}
    submission_id = path_parameters.get("submission_id")

    if not submission_id:
        logger.warning(
            json.dumps({
                "event": "get_submission_rejected",
                "request_id": request_id,
                "reason": "missing_submission_id",
            })
        )

        return response(
            400,
            {
                "error": "submission_id is required.",
                "request_id": request_id,
            },
        )

    # Retrieve submission from DynamoDB
    try:
        result = table.get_item(
            Key={
                "submission_id": submission_id
            }
        )

    except Exception as exc:
        logger.error(
            json.dumps({
                "event": "get_submission_failed",
                "request_id": request_id,
                "submission_id": submission_id,
                "error": str(exc),
            })
        )

        return response(
            500,
            {
                "error": "Unable to retrieve submission.",
                "request_id": request_id,
            },
        )

    item = result.get("Item")

    if not item:
        logger.warning(
            json.dumps({
                "event": "submission_not_found",
                "request_id": request_id,
                "submission_id": submission_id,
            })
        )

        return response(
            404,
            {
                "error": "Submission not found.",
                "submission_id": submission_id,
                "request_id": request_id,
            },
        )

    logger.info(
        json.dumps({
            "event": "submission_retrieved",
            "request_id": request_id,
            "submission_id": submission_id,
            "status": item.get("status"),
        })
    )

    return response(
        200,
        {
            "submission": item,
            "request_id": request_id,
        },
    )