import json
import logging
import os
import uuid
import boto3
from datetime import datetime, timedelta, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB

ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}

REQUIRED_FIELDS = [
    "student_ref",
    "course_code",
    "assessment",
    "file_name",
    "content_type",
    "file_size_bytes",
]
TABLE_NAME = os.environ.get("SUBMISSIONS_TABLE", "StudentSubmissions")
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT")

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=DYNAMODB_ENDPOINT if DYNAMODB_ENDPOINT else None,
)

table = dynamodb.Table(TABLE_NAME)

def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    request_id = getattr(context, "aws_request_id", str(uuid.uuid4()))

    logger.info(
        json.dumps({
            "event": "request_received",
            "request_id": request_id
        })
    )

    # ------------------------------------------------------
    # 1. Read request body
    # ------------------------------------------------------
    try:
        body = event.get("body", {})

        if isinstance(body, str):
            body = json.loads(body)

        if not isinstance(body, dict):
            raise ValueError("Request body must be a JSON object.")

    except (json.JSONDecodeError, ValueError):
        logger.warning(
            json.dumps({
                "event": "request_rejected",
                "request_id": request_id,
                "reason": "invalid_json"
            })
        )

        return response(
            400,
            {
                "error": "Request body must contain valid JSON.",
                "request_id": request_id,
            },
        )

    # ------------------------------------------------------
    # 2. Check required metadata
    # ------------------------------------------------------
    missing_fields = [
        field
        for field in REQUIRED_FIELDS
        if field not in body or body[field] in (None, "")
    ]

    if missing_fields:
        logger.warning(
            json.dumps({
                "event": "request_rejected",
                "request_id": request_id,
                "reason": "missing_fields",
                "fields": missing_fields,
            })
        )

        return response(
            400,
            {
                "error": "Missing required fields.",
                "fields": missing_fields,
                "request_id": request_id,
            },
        )

    # ------------------------------------------------------
    # 3. Validate file size
    # ------------------------------------------------------
    try:
        file_size = int(body["file_size_bytes"])
    except (TypeError, ValueError):
        return response(
            400,
            {
                "error": "file_size_bytes must be an integer.",
                "request_id": request_id,
            },
        )

    if file_size <= 0:
        return response(
            400,
            {
                "error": "File size must be greater than zero.",
                "request_id": request_id,
            },
        )

    if file_size > MAX_FILE_SIZE:
        return response(
            400,
            {
                "error": "File exceeds the 2 MB maximum size.",
                "request_id": request_id,
            },
        )

    # ------------------------------------------------------
    # 4. Validate content type and extension
    # ------------------------------------------------------
    content_type = str(body["content_type"]).lower().strip()
    file_name = str(body["file_name"]).lower().strip()

    if content_type not in ALLOWED_CONTENT_TYPES:
        return response(
            400,
            {
                "error": "Unsupported file type. Only PDF, DOC and DOCX are allowed.",
                "request_id": request_id,
            },
        )

    expected_extension = ALLOWED_CONTENT_TYPES[content_type]

    if not file_name.endswith(expected_extension):
        return response(
            400,
            {
                "error": (
                    f"File extension does not match content type. "
                    f"Expected {expected_extension}."
                ),
                "request_id": request_id,
            },
        )

    # ------------------------------------------------------
    # 5. Create submission
    # ------------------------------------------------------
    submission_id = str(uuid.uuid4())

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=15)

    submission = {
        "submission_id": submission_id,
        "student_ref": str(body["student_ref"]),
        "course_code": str(body["course_code"]),
        "assessment": str(body["assessment"]),
        "file_name": str(body["file_name"]),
        "content_type": content_type,
        "file_size_bytes": file_size,
        "status": "PENDING",
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "request_id": request_id,
    }

    logger.info(
        json.dumps({
            "event": "submission_created",
            "request_id": request_id,
            "submission_id": submission_id,
            "status": "PENDING",
        })
    )

    #========================================================================================================
    

        # ------------------------------------------------------
    # 6. Persist PENDING submission
    # ------------------------------------------------------
    try:
        table.put_item(
            Item=submission,
            ConditionExpression="attribute_not_exists(submission_id)",
        )

    except Exception as exc:
        logger.error(
            json.dumps({
                "event": "persistence_failed",
                "request_id": request_id,
                "submission_id": submission_id,
                "error": str(exc),
            })
        )

        return response(
            500,
            {
                "error": "Unable to create submission.",
                "request_id": request_id,
            },
        )

    logger.info(
        json.dumps({
            "event": "submission_persisted",
            "request_id": request_id,
            "submission_id": submission_id,
            "status": "PENDING",
        })
    )
    
    return response(
        201,
        {
            "message": "Upload request accepted.",
            "submission_id": submission_id,
            "status": "PENDING",
            "expires_at": expires_at.isoformat(),
            "request_id": request_id,
        },
    )