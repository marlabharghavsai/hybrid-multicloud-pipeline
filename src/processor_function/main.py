import base64
import json
import boto3
import os

def process_event(event, context):
    data = base64.b64decode(event["data"]).decode()
    record = json.loads(data)

    dynamodb = boto3.client(
        "dynamodb",
        endpoint_url=os.environ["DYNAMODB_ENDPOINT"]
    )

    dynamodb.put_item(
        TableName="processed-records",
        Item={
            "recordId":{"S":record["recordId"]},
            "userEmail":{"S":record["userEmail"]},
            "value":{"N":str(record["value"])},
            "processedAt":{"S":"timestamp"}
        }
    )
