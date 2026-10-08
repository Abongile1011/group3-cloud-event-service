# ADR-002: Validate locally instead of deploying to live AWS

**Decision:** The final system is validated with AWS SAM Local and DynamoDB Local instead of a live AWS deployment.

**Context:** The group did not have an approved AWS account or live AWS credentials for the milestone, and cloud cost had to be controlled.

**Options:**
1. Live AWS deployment. Not possible without an approved account and credentials.
2. Local emulation with AWS SAM Local and DynamoDB Local. Chosen.
3. In-memory mocks only. Rejected because they would not exercise a real persistence layer.

**Rationale:** Local emulation shows the application behaviour and keeps a clear mapping to the intended AWS architecture, while respecting the cost-control requirement.

**Consequences:** IAM permissions, API Gateway deployment, CloudWatch, S3 event delivery and the EventBridge schedule are not validated live. Local results do not prove these AWS integrations will work in the cloud. The report states this limitation.

**Evidence:** Report section "Limitations", tests/integration/test_submission_flow.py, evidence/final/test-unit.txt.
