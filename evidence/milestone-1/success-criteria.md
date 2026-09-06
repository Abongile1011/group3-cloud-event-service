# Milestone 1 Success Criteria

## Functional Criteria

| ID | Criterion | How it will be proven |
|----|-----------|------------------------|
| F1 | The service accepts one file when all required metadata, file type and size are valid. | Upload a valid PDF/DOCX/TXT and show an accepted response. |
| F2 | The service rejects a missing file, unsupported type, unsafe name or oversized file with a safe meaningful error. | Run invalid upload cases and show rejection plus no accepted submission state. |
| F3 | The service stores every accepted file in durable object storage. | Retrieve/show the stored object using its storage key. |
| F4 | Every accepted upload receives a unique submission/correlation ID. | Show the same ID in response, logs and metadata record. |
| F5 | The service stores submission metadata separately from the file content. | Show metadata containing course, assessment, file name, storage key, status and timestamp. |
| F6 | The system produces structured logs for accepted, rejected and failed upload execution. | Show logs with status, timestamp and submission ID where applicable. |

## Quality Criteria

| ID | Criterion | How it will be proven |
|----|-----------|------------------------|
| Q1 | A team member can reproduce the upload environment from documented prerequisites and commands. | Clean-machine/project reproduction using README instructions. |
| Q2 | No passwords, access keys, tokens, real sensitive student files or populated secret files appear in repository/report/screenshots. | Repository/manual secret and data check. |
| Q3 | Storage and processing permissions follow least privilege where supported. | Permission/configuration evidence and security checklist. |
| Q4 | At least one storage/dependency failure produces an observable safe error or recovery behaviour. | Controlled failure test, such as storage unavailable/permission denied, with logs and response. |
| Q5 | The team can explain storage/request/logging cost assumptions and can stop/delete resources after evidence is collected. | Cost note, resource inventory and teardown procedure. |
| Q6 | Architecture, event contract, tests and contribution evidence are version controlled. | Repository paths, commits/reviews and milestone evidence pack. |
