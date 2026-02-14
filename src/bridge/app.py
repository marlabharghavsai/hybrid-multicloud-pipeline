import boto3
import os
import time
import json
from google.cloud import pubsub_v1

print("🚀 Bridge started...")

# ------------------------------------------------------------------
# LocalStack clients
# ------------------------------------------------------------------

sqs = boto3.client(
    "sqs",
    endpoint_url="http://localstack:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

s3 = boto3.client(
    "s3",
    endpoint_url="http://localstack:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

# ------------------------------------------------------------------
# IMPORTANT FIX:
# Retry until queue exists (LocalStack startup delay)
# ------------------------------------------------------------------

queue_name = "data-processing-queue"
queue_url = None

print("⏳ Waiting for SQS queue...")

while not queue_url:
    try:
        queue_url = sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]
    except Exception:
        print("⌛ Queue not ready yet...")
        time.sleep(3)

print(f"✅ Using queue URL: {queue_url}")

# ------------------------------------------------------------------
# GCP PubSub
# ------------------------------------------------------------------

publisher = pubsub_v1.PublisherClient()

topic_path = publisher.topic_path(
    os.environ["GCP_PROJECT_ID"],
    "localstack-events"
)

print(f"✅ Pub/Sub topic: {topic_path}")

# ------------------------------------------------------------------
# Main loop
# ------------------------------------------------------------------

while True:
    print("📥 Polling SQS...")

    try:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=5
        )
    except Exception as e:
        print(f"⚠️ Receive error: {e}")
        time.sleep(3)
        continue

    if "Messages" in response:
        for msg in response["Messages"]:
            try:
                body = json.loads(msg["Body"])

                # Ignore LocalStack TestEvent
                if body.get("Event") == "s3:TestEvent":
                    print("⚠️ Ignoring TestEvent")
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=msg["ReceiptHandle"]
                    )
                    continue

                record = body["Records"][0]
                bucket = record["s3"]["bucket"]["name"]
                key = record["s3"]["object"]["key"]

                print(f"📂 Fetching file: {bucket}/{key}")

                obj = s3.get_object(Bucket=bucket, Key=key)
                file_content = obj["Body"].read()

                print("📤 Publishing to Pub/Sub...")
                publisher.publish(topic_path, file_content)

                print("✅ Published!")

                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=msg["ReceiptHandle"]
                )

            except Exception as e:
                print(f"❌ Message processing error: {e}")

    time.sleep(3)
