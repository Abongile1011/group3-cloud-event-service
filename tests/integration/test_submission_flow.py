import json
import os
import sys
import uuid
from unittest.mock import MagicMock

import boto3


ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
)

REQUEST_UPLOAD_PATH = os.path.join(ROOT, "src", "request_upload")
PROCESS_UPLOAD_PATH = os.path.join(ROOT, "src", "process_upload")
GET_SUBMISSION_PATH = os.path.join(ROOT, "src", "get_submission")


def load_module(module_name, module_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        module_name,
        os.path.join(module_path, "app.py"),
    )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def test_valid_submission_end_to_end():
    os.environ["AWS_ACCESS_KEY_ID"] = "local"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "local"
    os.environ["AWS_DEFAULT_REGION"] = "af-south-1"
    os.environ["SUBMISSIONS_TABLE"] = "StudentSubmissions"
    os.environ["DYNAMODB_ENDPOINT"] = "http://localhost:8000"
    request_upload = load_module(
        "request_upload_app",
        REQUEST_UPLOAD_PATH,
    )

    process_upload = load_module(
        "process_upload_app",
        PROCESS_UPLOAD_PATH,
    )

    get_submission = load_module(
        "get_submission_app",
        GET_SUBMISSION_PATH,
    )

    # Use the real local DynamoDB emulator
    dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url="http://localhost:8000",
        region_name="af-south-1",
        aws_access_key_id="local",
        aws_secret_access_key="local",
    )

    table = dynamodb.Table("StudentSubmissions")

    context = MagicMock()
    context.aws_request_id = f"e2e-{uuid.uuid4()}"

    # STEP 1: Submit a valid request
    request_event = {
        "body": json.dumps({
            "student_ref": "E2E-TEST",
            "course_code": "4CPS501B",
            "assessment": "Milestone 3 E2E Test",
            "file_name": "submission.pdf",
            "content_type": "application/pdf",
            "file_size_bytes": 1048576,
        })
    }

    create_response = request_upload.lambda_handler(
        request_event,
        context,
    )

    assert create_response["statusCode"] == 201

    create_body = json.loads(create_response["body"])
    submission_id = create_body["submission_id"]

    try:
        # STEP 2: Confirm PENDING was persisted
        stored = table.get_item(
            Key={"submission_id": submission_id}
        )["Item"]

        assert stored["status"] == "PENDING"

        # STEP 3: Simulate successful S3 upload event
        process_event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {
                            "name": "student-submission-uploads"
                        },
                        "object": {
                            "key": (
                                f"uploads/{submission_id}/submission.pdf"
                            ),
                            "size": 1048576,
                            "content_type": "application/pdf",
                        },
                    }
                }
            ]
        }

        process_response = process_upload.lambda_handler(
            process_event,
            context,
        )

        assert process_response["statusCode"] == 200

        process_body = json.loads(process_response["body"])
        assert process_body["status"] == "ACCEPTED"

        # STEP 4: Retrieve the submission
        get_event = {
            "pathParameters": {
                "submission_id": submission_id
            }
        }

        get_response = get_submission.lambda_handler(
            get_event,
            context,
        )

        assert get_response["statusCode"] == 200

        get_body = json.loads(get_response["body"])

        assert (
            get_body["submission"]["submission_id"]
            == submission_id
        )

        assert get_body["submission"]["status"] == "ACCEPTED"

    finally:
        # Remove the test record after the automated test
        table.delete_item(
            Key={"submission_id": submission_id}
        )