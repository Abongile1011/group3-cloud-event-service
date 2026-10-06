# Cloud-Based Student File Upload Service

**4CPS501B — Cloud Computing (Distributed Computing Part B) — Group 3 Practical**
University of Zululand, Honours, Lecturer: Prof. Matthew O. Adigun

---

## What this is

A small cloud-based event service that lets a student upload one academic file for submission. The service validates the file and required metadata, stores the file in durable object storage, records submission metadata and structured logs, and returns an acknowledgement with a unique submission ID. See `evidence/milestone-1/` and `architecture/` for the full Milestone 1 proposal (team charter, problem definition, event contract, success criteria, architecture diagram and platform decision record).

## Team — Group 3

| Member | Student No. | Role |
|---|---|---|
| Abongile Sigidi | 202121130 | Architecture & Integration Lead |
| Mbalenhle Precide Shandu | 202209456 | Cloud Platform & Security Lead |
| Xolani Thwala | 202032283 | Function/Application Developer |
| Xolile Wendy Sibiya | 202223792 | Data & Observability Lead |
| Amanda Nokwanda Mlotshwa | 230011945 | QA, Cost & Documentation Lead |

## Repository structure
README.md
architecture/
diagrams/ Initial architecture diagram
decisions/ Architecture Decision Records (ADRs)
threat-model/ Security threat modelling notes
infra/ Infrastructure/deployment templates
src/ Application source code
tests/ Automated tests
evidence/
milestone-1/ Team charter, problem definition, event contract, success criteria, work plan
milestone-2/
milestone-3/
final/
report/ Final combined project report
scripts/ Helper/automation scripts
.env.example Template of required environment variables

## Platform

Preferred: AWS native serverless (API Gateway/S3 upload → Lambda → S3 + DynamoDB → CloudWatch).
Fallback: AWS SAM local development. See `architecture/decisions/ADR-001-platform-route.md`.

## Status

Milestone 1 — Team, Problem and Proposal: **complete**.

## Milestone 3 - Working Vertical Slice

### Overview

Milestone 3 implements a working local vertical slice of the student file submission service.

The demonstrated lifecycle is:

PENDING -> ACCEPTED
PENDING -> REJECTED
PENDING -> EXPIRED

Implemented components:

- RequestUploadFunction
- ProcessUploadFunction
- GetSubmissionFunction
- ExpirePendingFunction
- DynamoDB Local persistence
- Valid and invalid request handling
- Automated unit testing
- Automated end-to-end testing

### Local Requirements

The following tools are required:

- Python 3
- Docker Desktop
- AWS CLI
- AWS SAM CLI
- Git

Create and activate the Python virtual environment:

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

Install development dependencies:

    python -m pip install -r requirements-dev.txt

### Local AWS Configuration

Dummy credentials are used only for local emulation:

    $env:AWS_ACCESS_KEY_ID="local"
    $env:AWS_SECRET_ACCESS_KEY="local"
    $env:AWS_DEFAULT_REGION="af-south-1"

Real AWS credentials must not be committed to this repository.

### Start DynamoDB Local

Start the local DynamoDB container:

    docker run -d --name group3-dynamodb -p 8000:8000 amazon/dynamodb-local

If the container already exists, start it with:

    docker start group3-dynamodb

Confirm that it is running:

    docker ps

Check whether the StudentSubmissions table exists:

    aws dynamodb list-tables --endpoint-url http://localhost:8000

If the table does not exist, create it:

    aws dynamodb create-table `
      --table-name StudentSubmissions `
      --attribute-definitions AttributeName=submission_id,AttributeType=S `
      --key-schema AttributeName=submission_id,KeyType=HASH `
      --billing-mode PAY_PER_REQUEST `
      --endpoint-url http://localhost:8000

### Validate and Build

Validate the SAM template:

    sam validate --region af-south-1

Build the application:

    sam build --no-cached

If OneDrive locks the .aws-sam directory, use:

    Remove-Item -Recurse -Force .aws-sam
    sam build --no-cached

### Run a Valid Submission

Run:

    sam local invoke RequestUploadFunction -e events/valid_submission.json

Expected result:

    HTTP 201
    status = PENDING

Record the generated submission_id. The submission_id is used as the correlation identifier across the processing flow.

### Run an Invalid Submission

Run:

    sam local invoke RequestUploadFunction -e events/invalid_submission.json

Expected result:

    HTTP 400
    Unsupported file type. Only PDF, DOC and DOCX are allowed.

The invalid request must not create a durable submission record.

### Run the Automated Unit Test

Run:

    python -m pytest tests\unit\test_request_upload.py -v

Expected result:

    test_rejects_unsupported_file_type PASSED
    1 passed

### Run the Automated End-to-End Test

Make sure DynamoDB Local is running, then run:

    python -m pytest tests\integration\test_submission_flow.py -v -s

Expected result:

    test_valid_submission_end_to_end PASSED
    1 passed

The end-to-end test covers:

    RequestUpload -> PENDING -> ProcessUpload -> ACCEPTED -> GetSubmission

The test deletes its temporary test record after completion.

### Local Emulation Limitations

Milestone 3 currently uses local emulation rather than a live AWS deployment.

DynamoDB persistence is tested using DynamoDB Local.

ProcessUpload receives a simulated S3-shaped event containing object size and content-type metadata. Actual S3 object retrieval and S3 event delivery are not validated by the current local test.

ExpirePending is invoked locally. The real EventBridge Scheduler trigger is not validated.

AWS IAM permissions, API Gateway cloud deployment, CloudWatch integration and live AWS deployment are not validated in the current local environment.

Therefore, successful local tests demonstrate the application vertical slice but do not prove that all AWS-specific integrations and IAM permissions will work in a live AWS environment.

### Reproduction Evidence

A second group member should follow these README instructions and reproduce the Milestone 3 vertical slice.

The reproducing member should successfully:

1. Start DynamoDB Local.
2. Validate and build the SAM application.
3. Run the valid submission.
4. Run the automated unit test.
5. Run the automated end-to-end test.

The reproducing member should retain terminal evidence showing the successful commands and test results.
