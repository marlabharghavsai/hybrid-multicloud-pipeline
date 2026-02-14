# Hybrid Multi-Cloud Data Processing Pipeline (LocalStack + GCP)

## Project Overview

This project demonstrates a **Hybrid Multi-Cloud Event-Driven Data Pipeline** that integrates:

* **LocalStack (AWS Simulation)** → S3, SQS, DynamoDB
* **Google Cloud Platform (GCP)** → Pub/Sub, Cloud Functions, Cloud SQL
* **Terraform** → Infrastructure as Code across multiple cloud providers
* **Docker Compose** → Environment orchestration
* **Bridge Service** → Cross-cloud message forwarding

The main objective is to simulate a real-world enterprise architecture where data originates in one cloud (AWS) and is processed in another (GCP).

---

## Architecture Overview

```
LocalStack S3  →  SQS Queue  →  Bridge Service  →  GCP Pub/Sub
                                          ↓
                                   Cloud Function
                                          ↓
                            Cloud SQL + DynamoDB
```

### Flow Explanation

1. A JSON file is uploaded into **LocalStack S3**.
2. S3 sends an event notification to **SQS**.
3. The **Bridge Application** polls SQS.
4. The bridge publishes the message to **GCP Pub/Sub**.
5. A **Cloud Function** processes the data.
6. Processed data is written into:

   * Cloud SQL (PostgreSQL)
   * LocalStack DynamoDB

---

## Technologies Used

* Docker & Docker Compose
* Terraform (Multi-Provider Setup)
* LocalStack
* Python (Bridge + Cloud Function)
* Google Cloud Platform
* AWS SDK (Boto3)

---

## Project Structure

```
hybrid-multicloud-pipeline
├── docker-compose.yml
├── .env.example
├── submission.json
├── README.md
├── terraform/
│   ├── providers.tf
│   ├── variables.tf
│   ├── localstack.tf
│   └── gcp.tf
└── src/
    ├── bridge/
    │   ├── Dockerfile
    │   └── app.py
    └── processor_function/
        ├── main.py
        ├── requirements.txt
        └── function.zip
```

---

## Step-by-Step Implementation

---

## Environment Setup

Install the following:

* Docker
* Terraform
* AWS CLI
* Google Cloud CLI

Authenticate GCP:

```
gcloud auth login
```

---

## Docker Compose Setup

`docker-compose.yml` launches:

* LocalStack container
* Bridge container

LocalStack services enabled:

```
s3
sqs
dynamodb
iam
```

Key features:

* Port `4566` exposed
* Persistent volume mounted
* Healthcheck enabled

Run:

```
docker-compose up --build
```

---

## Terraform Infrastructure

All infrastructure lives inside `/terraform`.

### Providers

`providers.tf` defines:

* AWS provider pointing to LocalStack endpoints
* Google provider for real GCP resources

---

### LocalStack Resources (localstack.tf)

Terraform provisions:

* S3 Bucket → `hybrid-cloud-bucket`
* SQS Queue → `data-processing-queue`
* DynamoDB Table → `processed-records`

This simulates AWS infrastructure locally.

---

### GCP Resources (gcp.tf)

Terraform provisions:

* Pub/Sub Topic → `localstack-events`
* Cloud SQL PostgreSQL instance
* Database → `pipelinedb`
* Cloud Function (Gen2)
* Custom Service Account
* Storage Bucket for Function Code

---

### Deploy Infrastructure

```
cd terraform
terraform init
terraform apply
```

---

## Bridge Application

The bridge acts as the **cross-cloud connector**.

### Responsibilities

* Poll LocalStack SQS queue
* Extract S3 event payload
* Fetch object data from S3
* Publish message to GCP Pub/Sub
* Delete processed message

### Why Bridge Exists

GCP cannot directly listen to LocalStack events.

Bridge provides:

* Decoupling
* Retry capability
* Cross-provider communication

---

### Bridge Container

Located in:

```
src/bridge/
```

Runs automatically through Docker Compose.

---

## Cloud Function (Processor)

Triggered by Pub/Sub messages.

### Responsibilities

1. Decode message
2. Parse JSON data
3. Add processing timestamp
4. Write to Cloud SQL
5. Write to DynamoDB

Location:

```
src/processor_function/main.py
```

---

## Input Event Format

Example `test-event.json`:

```json
{
  "recordId": "xyz-789",
  "userEmail": "test@example.com",
  "value": 120
}
```

---

## Trigger Pipeline

Upload file:

```
awslocal s3 cp test-event.json s3://hybrid-cloud-bucket/
```

Expected flow:

S3 → SQS → Bridge → Pub/Sub → Cloud Function → Database + DynamoDB

---

## Verification Steps

### Check SQS Message

```
awslocal sqs receive-message --queue-url <QUEUE_URL>
```

### Check Pub/Sub

```
gcloud pubsub subscriptions pull <SUB_NAME>
```

### Check DynamoDB

```
awslocal dynamodb get-item \
--table-name processed-records \
--key '{"recordId":{"S":"xyz-789"}}'
```

### Check Cloud SQL

```
SELECT * FROM records WHERE id='xyz-789';
```

---

## Environment Variables

Example `.env.example`:

```
GCP_PROJECT_ID="your-project"
GCP_REGION="us-central1"
PATH_TO_GCP_KEYFILE="./key.json"

AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1
```

---

## Architectural Decisions

### Event-Driven Design

Using queues and topics ensures:

* Loose coupling
* Fault tolerance
* Scalability

---

### Why SQS + Pub/Sub?

They allow buffering between cloud providers, preventing tight integration and improving resilience.

---

### Infrastructure as Code

Terraform enables:

* Single codebase for multi-cloud
* Reproducible deployments
* Version control of infrastructure

---

## Known Limitations

* GCP service accounts must exist for Cloud Functions deployment.
* Cross-cloud communication requires correct IAM roles.
* LocalStack networking differs from real AWS.

---

## Scaling Considerations

If processing thousands of files per minute:

* Increase Cloud Function concurrency
* Add Pub/Sub dead-letter topics
* Batch SQS polling
* Use Cloud SQL connection pooling

---

## Alternative Design (Without Bridge)

Instead of polling:

* Push events via HTTPS webhook
* Use EventArc or Cloud Run

Trade-off:

| Bridge Polling | Direct Push        |
| -------------- | ------------------ |
| Simple         | Faster             |
| More control   | Less latency       |
| Slight delay   | Complex networking |

---

## Submission Checklist

✔ docker-compose.yml
✔ Terraform directory
✔ Bridge Dockerfile
✔ Cloud Function code
✔ submission.json
✔ .env.example

---
