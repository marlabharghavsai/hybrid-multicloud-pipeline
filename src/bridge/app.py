import boto3
import os
import time
from google.cloud import pubsub_v1

sqs = boto3.client("sqs", endpoint_url="http://localstack:4566")

queue_url = sqs.get_queue_url(
    QueueName="data-processing-queue"
)["QueueUrl"]

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(
    os.environ["GCP_PROJECT_ID"],
    "localstack-events"
)

while True:
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5
    )

    if "Messages" in response:
        for msg in response["Messages"]:
            data = msg["Body"].encode("utf-8")

            publisher.publish(topic_path, data)

            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=msg["ReceiptHandle"]
            )

    time.sleep(3)
