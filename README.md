Cloud-Based Student File Upload Service

4CPS501B — Cloud Computing (Distributed Computing Part B) — Group 3 Practical University of Zululand, Honours, Lecturer: [add lecturer's name]

What this is

A small cloud-based event service that lets a student upload one academic file for submission. The service validates the file and required metadata, stores the file in durable object storage, records submission metadata and structured logs, and returns an acknowledgement with a unique submission ID. See evidence/milestone-1/ and architecture/ for the full Milestone 1 proposal (team charter, problem definition, event contract, success criteria, architecture diagram and platform decision record).

Team — Group 3
Member	Student No.	Role
Abongile Sigidi	202121130	Architecture & Integration Lead
Mbalenhle Precide Shandu	202209456	Cloud Platform & Security Lead
Xolani Thwala	202032283	Function/Application Developer
Xolile Wendy Sibiya	202223792	Data & Observability Lead
Amanda Nokwanda Mlotshwa	230011945	QA, Cost & Documentation Lead
Repository structure
README.md
architecture/
  diagrams/           Initial architecture diagram
  decisions/          Architecture Decision Records (ADRs)
threat-model/         Security threat modelling notes
infra/                Infrastructure/deployment templates
src/                  Application source code
tests/                Automated tests
evidence/
  milestone-1/        Team charter, problem definition, event contract, success criteria, work plan
  milestone-2/
  milestone-3/
  final/
report/               Final combined project report
scripts/              Helper/automation scripts
.env.example          Template of required environment variables (no real secrets)
Platform

Preferred: AWS native serverless (API Gateway/S3 upload → Lambda → S3 + DynamoDB → CloudWatch). Fallback: AWS SAM local development. See architecture/decisions/ADR-001-platform-route.md.

Status

Milestone 1 — Team, Problem and Proposal: complete.# group3-cloud-event-service
