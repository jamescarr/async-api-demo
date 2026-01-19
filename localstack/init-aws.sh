#!/bin/bash
# Initialize LocalStack with SQS queues

echo "Creating SQS queues..."

# Main order events queue (consumed by the order consumer)
awslocal sqs create-queue --queue-name order-events

# Dead letter queue for failed messages
awslocal sqs create-queue --queue-name order-events-dlq

echo "SQS queues created:"
awslocal sqs list-queues
