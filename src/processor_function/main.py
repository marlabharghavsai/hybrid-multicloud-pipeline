import base64
import json
import os
import boto3
import psycopg2
from datetime import datetime


# ----------------------------------------------------------
# MAIN CLOUD FUNCTION ENTRY
# ----------------------------------------------------------
def process_event(event, context):

    print("🔥 Cloud Function triggered")

    # ------------------------------------------------------
    # Decode Pub/Sub message
    # ------------------------------------------------------
    data = base64.b64decode(event["data"]).decode("utf-8")
    record = json.loads(data)

    print("📥 Received record:", record)

    # ------------------------------------------------------
    # Transform data
    # ------------------------------------------------------
    processed_timestamp = datetime.utcnow().isoformat()

    record_id = record["recordId"]
    user_email = record["userEmail"]
    value = record["value"]

    # ------------------------------------------------------
    # Write to CLOUD SQL (PostgreSQL)
    # ------------------------------------------------------
    try:
        print("🗄️ Connecting to Cloud SQL...")

        conn = psycopg2.connect(
            host=f"/cloudsql/{os.environ['DB_INSTANCE']}",
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASS"]
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO records (id, user_email, value, processed_at)
            VALUES (%s,%s,%s,%s)
            ON CONFLICT (id) DO NOTHING;
            """,
            (record_id, user_email, value, processed_timestamp)
        )

        conn.commit()
        cursor.close()
        conn.close()

        print("✅ Inserted into Cloud SQL")

    except Exception as e:
        print("❌ Cloud SQL error:", str(e))

    # ------------------------------------------------------
    # Write BACK to LocalStack DynamoDB
    # ------------------------------------------------------
    try:
        print("📦 Writing to LocalStack DynamoDB...")

        dynamodb = boto3.client(
            "dynamodb",
            endpoint_url=os.environ["DYNAMODB_ENDPOINT"],
            region_name="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test"
        )

        dynamodb.put_item(
            TableName="processed-records",
            Item={
                "recordId": {"S": record_id},
                "userEmail": {"S": user_email},
                "value": {"N": str(value)},
                "processedAt": {"S": processed_timestamp}
            }
        )

        print("✅ Inserted into DynamoDB")

    except Exception as e:
        print("❌ DynamoDB error:", str(e))

    print("🎉 Processing complete")
