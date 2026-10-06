import json
import logging
import os
from datetime import datetime, timezone

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get("SUBMISSIONS_TABLE", "StudentSubmissions")
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT")

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=DYNAMODB_ENDPOINT if DYNAMODB_ENDPOINT else None,
)

table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    request_id = getattr(context, "aws_request_id", "unknown")
    now = datetime.now(timezone.utc)

    logger.info(
        json.dumps({
            "event": "expiry_check_started",
            "request_id": request_id,
            "checked_at": now.isoformat(),
        })
    )

    try:
        result = table.scan()

    except Exception as exc:
        logger.error(
            json.dumps({
                "event": "expiry_scan_failed",
                "request_id": request_id,
                "error": str(exc),
            })
        )

        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Unable to scan pending submissions."
            }),
        }

    expired_count = 0

    for submission in result.get("Items", []):
        submission_id = submission.get("submission_id")
        status = submission.get("status")
        expires_at = submission.get("expires_at")

        # Ignore records that are no longer PENDING
        if status != "PENDING":
            continue

        if not expires_at:
            continue

        try:
            expiry_time = datetime.fromisoformat(expires_at)

            if expiry_time.tzinfo is None:
                expiry_time = expiry_time.replace(tzinfo=timezone.utc)

        except ValueError:
            logger.warning(
                json.dumps({
                    "event": "invalid_expiry_timestamp",
                    "request_id": request_id,
                    "submission_id": submission_id,
                })
            )
            continue

        if expiry_time > now:
            continue

        try:
            table.update_item(
                Key={
                    "submission_id": submission_id
                },
                UpdateExpression="SET #status = :expired",
                ConditionExpression="#status = :pending",
                ExpressionAttributeNames={
                    "#status": "status"
                },
                ExpressionAttributeValues={
                    ":expired": "EXPIRED",
                    ":pending": "PENDING",
                },
            )

            expired_count += 1

            logger.info(
                json.dumps({
                    "event": "submission_expired",
                    "request_id": request_id,
                    "submission_id": submission_id,
                    "old_status": "PENDING",
                    "new_status": "EXPIRED",
                    "expires_at": expires_at,
                })
            )

        except Exception as exc:
            logger.error(
                json.dumps({
                    "event": "expiry_update_failed",
                    "request_id": request_id,
                    "submission_id": submission_id,
                    "error": str(exc),
                })
            )

    logger.info(
        json.dumps({
            "event": "expiry_check_completed",
            "request_id": request_id,
            "expired_count": expired_count,
        })
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Expiry check completed.",
            "expired_count": expired_count,
        }),
    }