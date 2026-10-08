# ADR-003: Store uploaded files in a local folder during development

**Decision:** In local development, UploadFileFunction stores files in a local folder (LOCAL_STORAGE_PATH) instead of Amazon S3. Amazon S3 remains the cloud target.

**Context:** There is no live AWS account, but the upload function must still receive and keep the real file so it can be checked against the declared metadata.

**Options:**
1. Amazon S3. This is the target, but it needs a live AWS account.
2. A local folder. Chosen.
3. Store the file inside the DynamoDB record. Rejected because a DynamoDB item is limited to 400 KB and is not suited to files.

**Rationale:** A local folder keeps the upload flow testable without AWS, and the code is written so S3 stays the target service.

**Consequences:** Stored files may not survive after the SAM Local container stops. The local-storage folder is excluded from Git. S3 delivery and S3 permissions are untested. The upload response shows Storage: LOCAL_DEVELOPMENT.

**Evidence:** src/upload_file/app.py (LOCAL_STORAGE_PATH), .gitignore, Normal Case 1 screenshot in the report.
