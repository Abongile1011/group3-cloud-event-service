# ADR-001: Platform / Environment Route

## Status
Accepted (Milestone 1)

## Decision
Preferred route: AWS native serverless using an upload endpoint/trigger, AWS Lambda for validation/processing, Amazon S3 for durable file storage, DynamoDB for submission metadata, and CloudWatch for logs.

Fallback route: AWS SAM local development with lecturer-approved local storage/emulation where required.

## Context
The project must demonstrate event-driven processing, persistence, observability, security reasoning, reproducibility and cost control. The selected route must also fit a short practical window and avoid dependence on unapproved personal payment details.

## Options Compared

| Criterion | AWS native serverless (Preferred) | AWS SAM local (Fallback) |
|---|---|---|
| Endpoint/processing | API Gateway/S3 event + Lambda provide a direct managed/serverless upload path. | Local API and Lambda-style validation can be built/invoked using SAM CLI. |
| Persistence | Amazon S3 stores file objects; DynamoDB stores submission metadata. | Local/mock storage can support development; unverified cloud storage behaviour must be stated. |
| Observability | CloudWatch supports structured upload logs and metrics. | Local function output/logging supports development evidence but not all cloud observability behaviour. |
| Security learning | Direct IAM, S3 access policy and managed-service permission experience. | Partial IAM/service fidelity; storage and permission assumptions must be documented. |
| Reproducibility | Infrastructure template plus documented deploy/delete and bucket/table setup. | template.yaml, source, event samples and tests can be version controlled. |
| Cost exposure | Possible request, storage and logging charges; requires approved account/sandbox and teardown. | Runs locally; avoids routine public-cloud charges. |
| Main risk | Account access, billing, S3/IAM configuration and incomplete teardown. | Does not reproduce every S3/cloud integration or IAM behaviour. |

## Rationale
AWS native serverless is preferred because it maps naturally to a file-upload event service. An HTTP/API or S3 upload flow can trigger a small stateless Lambda function, Amazon S3 is designed for durable object storage, DynamoDB can retain the small submission metadata record, and CloudWatch can provide traceable logs. AWS SAM local remains a useful fallback for developing and testing the Lambda/API logic without depending on continuous public-cloud access.

## Consequences
- The team must keep the processor stateless and place uploaded files and submission metadata in durable storage.
- The team must document deployment and teardown, not only application code.
- The team must prove traceability using a request/correlation ID.
- If the fallback is used, the report must clearly distinguish emulated/local behaviour from behaviour validated in the real cloud.
