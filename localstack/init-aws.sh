#!/bin/bash
set -e

echo "Creating SQS queues..."

# Create the order fulfillment queue (receives events from Redpanda Connect)
awslocal sqs create-queue --queue-name order-fulfillment-events

# Create DLQ for failed messages
awslocal sqs create-queue --queue-name order-fulfillment-events-dlq

# Create notification queue for downstream consumers
awslocal sqs create-queue --queue-name order-notifications

echo "SQS queues created successfully!"
awslocal sqs list-queues

