import base64
import json
import logging
import mimetypes
import os
from pathlib import Path

import boto3


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
}

TABLE_NAME = os.environ.get(
    "SUBMISSIONS_TABLE",
    "StudentSubmissions"
)

DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT")

# Local storage is used only for Milestone 3 development.
# Amazon S3 remains the target cloud storage service.
LOCAL_STORAGE_PATH = os.environ.get(
    "LOCAL_STORAGE_PATH",
    "/tmp/local-storage"
)


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# ---------------------------------------------------------
# DynamoDB
# ---------------------------------------------------------

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=DYNAMODB_ENDPOINT if DYNAMODB_ENDPOINT else None,
)

table = dynamodb.Table(TABLE_NAME)


# ---------------------------------------------------------
# HTTP response helper
# ---------------------------------------------------------

def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body),
    }


# ---------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------

def lambda_handler(event, context):

    request_id = getattr(
        context,
        "aws_request_id",
        "unknown"
    )

    logger.info(
        json.dumps({
            "event": "file_upload_received",
            "request_id": request_id,
        })
    )

    try:

        # -------------------------------------------------
        # 1. Get submission ID
        # -------------------------------------------------

        path_parameters = event.get("pathParameters") or {}

        submission_id = path_parameters.get(
            "submission_id"
        )

        if not submission_id:

            return response(400, {
                "message": "submission_id is required."
            })


        # -------------------------------------------------
        # 2. Get uploaded file
        # -------------------------------------------------

        body = event.get("body")

        if not body:

            return response(400, {
                "message": "No file was provided.",
                "submission_id": submission_id
            })


        # -------------------------------------------------
        # 3. Decode Base64 file
        # -------------------------------------------------

        try:
            file_bytes = base64.b64decode(
                body,
                validate=True
            )

        except Exception:

            logger.warning(
                json.dumps({
                    "event": "invalid_file_data",
                    "request_id": request_id,
                    "submission_id": submission_id,
                })
            )

            return response(400, {
                "message": "Invalid file data.",
                "submission_id": submission_id
            })


        # -------------------------------------------------
        # 4. Validate actual file size
        # -------------------------------------------------

        actual_file_size = len(file_bytes)

        if actual_file_size == 0:

            return response(400, {
                "message": "Uploaded file is empty.",
                "submission_id": submission_id
            })

        if actual_file_size > MAX_FILE_SIZE:

            return response(400, {
                "message": "File exceeds the maximum size of 2 MB.",
                "submission_id": submission_id
            })


        # -------------------------------------------------
        # 5. Get and validate file name
        # -------------------------------------------------

        headers = event.get("headers") or {}

        file_name = (
            headers.get("x-file-name")
            or headers.get("X-File-Name")
            or "submission.pdf"
        )

        # Prevent path traversal.
        file_name = Path(file_name).name

        extension = Path(file_name).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:

            return response(400, {
                "message": "Unsupported file type.",
                "submission_id": submission_id
            })


        # -------------------------------------------------
        # 6. Determine actual content type
        # -------------------------------------------------

        uploaded_content_type, _ = mimetypes.guess_type(
            file_name
        )

        if uploaded_content_type is None:
            uploaded_content_type = (
                "application/octet-stream"
            )


        # -------------------------------------------------
        # 7. Retrieve original DynamoDB record
        # -------------------------------------------------

        try:

            result = table.get_item(
                Key={
                    "submission_id": submission_id
                }
            )

        except Exception as error:

            logger.error(
                json.dumps({
                    "event": "submission_lookup_failed",
                    "request_id": request_id,
                    "submission_id": submission_id,
                    "error": str(error),
                })
            )

            return response(500, {
                "message": "Unable to retrieve submission.",
                "submission_id": submission_id
            })


        submission = result.get("Item")

        if not submission:

            logger.warning(
                json.dumps({
                    "event": "submission_not_found",
                    "request_id": request_id,
                    "submission_id": submission_id,
                })
            )

            return response(404, {
                "message": "Submission not found.",
                "submission_id": submission_id
            })


        # -------------------------------------------------
        # 8. Only process PENDING submissions
        # -------------------------------------------------

        current_status = submission.get("status")

        if current_status != "PENDING":

            logger.warning(
                json.dumps({
                    "event": "submission_not_pending",
                    "request_id": request_id,
                    "submission_id": submission_id,
                    "status": current_status,
                })
            )

            return response(409, {
                "message": (
                    "Submission is not in PENDING status."
                ),
                "submission_id": submission_id,
                "status": current_status
            })


        # -------------------------------------------------
        # 9. Save actual uploaded file locally
        # -------------------------------------------------

        submission_directory = (
            Path(LOCAL_STORAGE_PATH)
            / submission_id
        )

        submission_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        file_path = (
            submission_directory
            / file_name
        )

        with open(
            file_path,
            "wb"
        ) as uploaded_file:

            uploaded_file.write(
                file_bytes
            )


        logger.info(
            json.dumps({
                "event": "actual_file_stored",
                "request_id": request_id,
                "submission_id": submission_id,
                "file_name": file_name,
                "actual_file_size": actual_file_size,
                "actual_content_type": uploaded_content_type,
                "storage": "LOCAL_DEVELOPMENT",
            })
        )


        # -------------------------------------------------
        # 10. Read originally declared metadata
        # -------------------------------------------------

        try:
            declared_size = int(
                submission.get(
                    "file_size_bytes",
                    0
                )
            )

        except (TypeError, ValueError):
            declared_size = 0

        declared_content_type = submission.get(
            "content_type"
        )

        declared_file_name = submission.get(
            "file_name"
        )


        # -------------------------------------------------
        # 11. Compare actual file with declaration
        # -------------------------------------------------

        size_matches = (
            actual_file_size
            == declared_size
        )

        content_type_matches = (
            uploaded_content_type
            == declared_content_type
        )

        file_name_matches = (
            file_name
            == declared_file_name
        )


        # -------------------------------------------------
        # 12. Decide ACCEPTED or REJECTED
        # -------------------------------------------------

        if (
            size_matches
            and content_type_matches
            and file_name_matches
        ):

            new_status = "ACCEPTED"

            reason = (
                "Uploaded file matches the "
                "original submission metadata."
            )

        else:

            new_status = "REJECTED"

            reason = (
                "Uploaded file does not match the "
                "original submission metadata."
            )


        # -------------------------------------------------
        # 13. Log validation result
        # -------------------------------------------------

        logger.info(
            json.dumps({
                "event": "upload_validated",
                "request_id": request_id,
                "submission_id": submission_id,

                "declared_file_name":
                    declared_file_name,

                "actual_file_name":
                    file_name,

                "declared_size":
                    declared_size,

                "actual_size":
                    actual_file_size,

                "declared_content_type":
                    declared_content_type,

                "actual_content_type":
                    uploaded_content_type,

                "size_matches":
                    size_matches,

                "content_type_matches":
                    content_type_matches,

                "file_name_matches":
                    file_name_matches,

                "result":
                    new_status,
            })
        )


        # -------------------------------------------------
        # 14. Update DynamoDB status
        # -------------------------------------------------

        try:

            table.update_item(
                Key={
                    "submission_id":
                        submission_id
                },

                UpdateExpression=(
                    "SET #status = :new_status"
                ),

                ConditionExpression=(
                    "#status = :pending"
                ),

                ExpressionAttributeNames={
                    "#status": "status"
                },

                ExpressionAttributeValues={
                    ":new_status":
                        new_status,

                    ":pending":
                        "PENDING",
                },
            )

        except Exception as error:

            logger.error(
                json.dumps({
                    "event": "status_update_failed",
                    "request_id": request_id,
                    "submission_id": submission_id,
                    "error": str(error),
                })
            )

            return response(500, {
                "message": (
                    "Unable to update "
                    "submission status."
                ),
                "submission_id":
                    submission_id
            })


        # -------------------------------------------------
        # 15. Final trace log
        # -------------------------------------------------

        logger.info(
            json.dumps({
                "event":
                    "submission_status_updated",

                "request_id":
                    request_id,

                "submission_id":
                    submission_id,

                "old_status":
                    "PENDING",

                "new_status":
                    new_status,
            })
        )


        # -------------------------------------------------
        # 16. Return result to frontend
        # -------------------------------------------------

        return response(201, {

            "message":
                reason,

            "submission_id":
                submission_id,

            "file_name":
                file_name,

            "file_size_bytes":
                actual_file_size,

            "content_type":
                uploaded_content_type,

            "storage":
                "LOCAL_DEVELOPMENT",

            "status":
                new_status
        })


    except Exception as error:

        logger.exception(
            json.dumps({
                "event":
                    "upload_processing_failed",

                "request_id":
                    request_id,

                "error":
                    str(error),
            })
        )

        return response(500, {
            "message":
                "Internal server error."
        })