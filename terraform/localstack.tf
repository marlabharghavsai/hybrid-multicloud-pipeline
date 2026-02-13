############################
# S3 Bucket
############################
resource "aws_s3_bucket" "bucket" {
  bucket = "hybrid-cloud-bucket"
}

############################
# SQS Queue
############################
resource "aws_sqs_queue" "queue" {
  name = "data-processing-queue"
}

############################
# DynamoDB Table
############################
resource "aws_dynamodb_table" "table" {
  name         = "processed-records"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "recordId"

  attribute {
    name = "recordId"
    type = "S"
  }
}

############################
# Allow S3 to send to SQS
############################
resource "aws_sqs_queue_policy" "policy" {
  queue_url = aws_sqs_queue.queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = "*"
      Action = "SQS:SendMessage"
      Resource = aws_sqs_queue.queue.arn
    }]
  })
}

############################
# S3 Event Trigger → SQS
############################
resource "aws_s3_bucket_notification" "notification" {
  bucket = aws_s3_bucket.bucket.id

  queue {
    queue_arn = aws_sqs_queue.queue.arn
    events    = ["s3:ObjectCreated:*"]
  }
}
