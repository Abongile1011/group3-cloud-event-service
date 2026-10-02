import json
import os
import sys
from unittest.mock import MagicMock

# Allow the test to import RequestUploadFunction
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../src/request_upload")
    ),
)

import app


def test_rejects_unsupported_file_type():
    event = {
        "body": json.dumps(
            {
                "student_ref": "20260001",
                "course_code": "4CPS501B",
                "assessment": "Milestone 3",
                "file_name": "malware.exe",
                "content_type": "application/octet-stream",
                "file_size_bytes": 1048576,
            }
        )
    }

    context = MagicMock()
    context.aws_request_id = "unit-test-request-id"

    response = app.lambda_handler(event, context)

    assert response["statusCode"] == 400

    body = json.loads(response["body"])

    assert body["error"] == (
        "Unsupported file type. Only PDF, DOC and DOCX are allowed."
    )

    assert body["request_id"] == "unit-test-request-id"