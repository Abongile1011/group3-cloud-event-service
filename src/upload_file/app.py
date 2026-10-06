import base64
import json
import os
from pathlib import Path


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
}

# This is used only for local Milestone 3 development.
# Amazon S3 remains the target cloud storage service.
LOCAL_STORAGE_PATH = os.environ.get(
    "LOCAL_STORAGE_PATH",
    "/tmp/local-storage"
)


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    try:
        submission_id = event.get("pathParameters", {}).get("submission_id")

        if not submission_id:
            return response(400, {
                "message": "submission_id is required."
            })

        body = event.get("body")

        if not body:
            return response(400, {
                "message": "No file was provided."
            })

        # Browser sends the file as Base64.
        if event.get("isBase64Encoded", False):
            file_bytes = base64.b64decode(body)
        else:
            try:
                file_bytes = base64.b64decode(body)
            except Exception:
                return response(400, {
                    "message": "Invalid file data."
                })

        if len(file_bytes) == 0:
            return response(400, {
                "message": "Uploaded file is empty."
            })

        if len(file_bytes) > MAX_FILE_SIZE:
            return response(400, {
                "message": "File exceeds the maximum size of 10 MB."
            })

        headers = event.get("headers") or {}

        file_name = (
            headers.get("x-file-name")
            or headers.get("X-File-Name")
            or "submission.pdf"
        )

        extension = Path(file_name).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            return response(400, {
                "message": "Unsupported file type."
            })

        # Each submission gets its own directory.
        submission_directory = (
            Path(LOCAL_STORAGE_PATH) / submission_id
        )

        submission_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        file_path = submission_directory / file_name

        with open(file_path, "wb") as uploaded_file:
            uploaded_file.write(file_bytes)

        return response(201, {
            "message": "File uploaded successfully.",
            "submission_id": submission_id,
            "file_name": file_name,
            "file_size_bytes": len(file_bytes),
            "storage": "LOCAL_DEVELOPMENT"
        })

    except Exception as error:
        print(f"Upload error: {error}")

        return response(500, {
            "message": "Internal server error."
        })