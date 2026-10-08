import json
import logging
import os
from urllib.parse import unquote_plus

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

    logger.info(
        json.dumps({
            "event": "process_upload_received",
            "request_id": request_id,
        })
    )

    try:
        record = event["Records"][0]

        bucket_name = record["s3"]["bucket"]["name"]
        object_key = unquote_plus(
            record["s3"]["object"]["key"]
        )

    except (KeyError, IndexError, TypeError):
        logger.warning(
            json.dumps({
                "event": "invalid_s3_event",
                "request_id": request_id,
            })
        )

        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Invalid S3 event."
            }),
        }

    # Expected object key:
    # uploads/<submission_id>/submission.pdf

    key_parts = object_key.split("/")

    if len(key_parts) < 3:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Invalid upload object key."
            }),
        }

    submission_id = key_parts[1]

    logger.info(
        json.dumps({
            "event": "upload_identified",
            "request_id": request_id,
            "submission_id": submission_id,
            "bucket": bucket_name,
            "object_key": object_key,
        })
    )

    try:
        result = table.get_item(
            Key={
                "submission_id": submission_id
            }
        )

    except Exception as exc:
        logger.error(
            json.dumps({
                "event": "submission_lookup_failed",
                "request_id": request_id,
                "submission_id": submission_id,
                "error": str(exc),
            })
        )

        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Unable to retrieve submission."
            }),
        }

    submission = result.get("Item")

    if not submission:
        logger.warning(
            json.dumps({
                "event": "submission_not_found",
                "request_id": request_id,
                "submission_id": submission_id,
            })
        )

        return {
            "statusCode": 404,
            "body": json.dumps({
                "error": "Submission not found."
            }),
        }

    logger.info(
        json.dumps({
            "event": "submission_found_for_processing",
            "request_id": request_id,
            "submission_id": submission_id,
            "status": submission.get("status"),
        })
    )

        # Only PENDING submissions should be processed
    # Only PENDING submissions should be processed
    if submission.get("status") != "PENDING":
        logger.warning(
            json.dumps({
                "event": "submission_not_pending",
                "request_id": request_id,
                "submission_id": submission_id,
                "status": submission.get("status"),
            })
        )

        return {
            "statusCode": 409,
            "body": json.dumps({
                "error": "Submission is not in PENDING status.",
                "submission_id": submission_id,
                "status": submission.get("status"),
            }),
        }

    # Metadata reported by the simulated S3 event
    uploaded_size = record["s3"]["object"].get("size")
    uploaded_content_type = record["s3"]["object"].get("content_type")

    # Metadata originally declared by the student
    declared_size = int(submission.get("file_size_bytes"))
    declared_content_type = submission.get("content_type")

    size_matches = uploaded_size == declared_size
    content_type_matches = uploaded_content_type == declared_content_type

    if size_matches and content_type_matches:
        new_status = "ACCEPTED"
        reason = "Uploaded file metadata matches the original declaration."
    else:
        new_status = "REJECTED"
        reason = "Uploaded file metadata does not match the original declaration."

    logger.info(
        json.dumps({
            "event": "upload_validated",
            "request_id": request_id,
            "submission_id": submission_id,
            "declared_size": declared_size,
            "uploaded_size": uploaded_size,
            "declared_content_type": declared_content_type,
            "uploaded_content_type": uploaded_content_type,
            "result": new_status,
        })
    )

    try:
        table.update_item(
            Key={
                "submission_id": submission_id
            },
            UpdateExpression="SET #status = :new_status",
            ConditionExpression="#status = :pending",
            ExpressionAttributeNames={
                "#status": "status"
            },
            ExpressionAttributeValues={
                ":new_status": new_status,
                ":pending": "PENDING",
            },
        )

    except Exception as exc:
        logger.error(
            json.dumps({
                "event": "status_update_failed",
                "request_id": request_id,
                "submission_id": submission_id,
                "error": str(exc),
            })
        )

        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Unable to update submission status.",
                "submission_id": submission_id,
            }),
        }

    logger.info(
        json.dumps({
            "event": "submission_status_updated",
            "request_id": request_id,
            "submission_id": submission_id,
            "old_status": "PENDING",
            "new_status": new_status,
        })
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": reason,
            "submission_id": submission_id,
            "status": new_status,
        }),
    }
