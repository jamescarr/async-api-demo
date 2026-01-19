# AsyncAPI Demo - Command Runner
# Install just: https://github.com/casey/just

set dotenv-load

# Default recipe - show available commands
default:
    @just --list

# ─────────────────────────────────────────────────────────────
# Docker Compose
# ─────────────────────────────────────────────────────────────

# Start all services
up:
    docker compose up -d
    @echo "Services starting..."
    @echo "Redpanda Console: http://localhost:8080"
    @echo "LocalStack: http://localhost:4566"

# Stop all services
down:
    docker compose down

# View all logs
logs:
    docker compose logs -f

# View logs for a specific service
logs-service service:
    docker compose logs -f {{ service }}

# Build all services
build:
    docker compose build

# Rebuild and restart services
rebuild: build
    docker compose up -d

# Clean up volumes and prune
clean:
    docker compose down -v
    docker system prune -f

# ─────────────────────────────────────────────────────────────
# Service Logs (shortcuts)
# ─────────────────────────────────────────────────────────────

# View producer logs
producer-logs:
    docker compose logs -f producer

# View consumer logs
consumer-logs:
    docker compose logs -f consumer

# View Redpanda Connect logs
connect-logs:
    docker compose logs -f connect

# ─────────────────────────────────────────────────────────────
# SQS (LocalStack)
# ─────────────────────────────────────────────────────────────

# Check SQS messages in both queues
sqs-messages:
    @echo "=== Order Fulfillment Events Queue ==="
    aws --endpoint-url=http://localhost:4566 sqs receive-message \
        --queue-url http://localhost:4566/000000000000/order-fulfillment-events \
        --max-number-of-messages 5 2>/dev/null || echo "No messages"
    @echo ""
    @echo "=== Order Notifications Queue ==="
    aws --endpoint-url=http://localhost:4566 sqs receive-message \
        --queue-url http://localhost:4566/000000000000/order-notifications \
        --max-number-of-messages 5 2>/dev/null || echo "No messages"

# List SQS queues
sqs-queues:
    aws --endpoint-url=http://localhost:4566 sqs list-queues

# ─────────────────────────────────────────────────────────────
# Redpanda / Kafka
# ─────────────────────────────────────────────────────────────

# List all topics
topics:
    docker compose exec redpanda rpk topic list

# Describe a topic
topic-describe topic:
    docker compose exec redpanda rpk topic describe {{ topic }}

# Consume messages from a topic
consume topic:
    docker compose exec redpanda rpk topic consume {{ topic }}

# List consumer groups
groups:
    docker compose exec redpanda rpk group list

# Describe a consumer group
group-describe group:
    docker compose exec redpanda rpk group describe {{ group }}

# ─────────────────────────────────────────────────────────────
# AsyncAPI Spec Generation (from code)
# ─────────────────────────────────────────────────────────────

# Generate producer AsyncAPI spec from code
generate-producer-spec:
    cd producer && uv run producer asyncapi --yaml -o ../docs/asyncapi-producer.yaml
    @echo "✓ Generated docs/asyncapi-producer.yaml"

# Generate consumer AsyncAPI spec from code
generate-consumer-spec:
    cd consumer && uv run consumer asyncapi --yaml -o ../docs/asyncapi-consumer.yaml
    @echo "✓ Generated docs/asyncapi-consumer.yaml"

# Generate all AsyncAPI specs from code
generate-specs: generate-producer-spec generate-consumer-spec
    @echo "✓ All specs generated from code"

# Serve producer docs locally (interactive viewer)
serve-producer-docs:
    cd producer && uv run faststream docs serve app.main:app

# Serve consumer docs locally (interactive viewer)
serve-consumer-docs:
    cd consumer && uv run faststream docs serve app.main:app

# ─────────────────────────────────────────────────────────────
# AsyncAPI CLI Tools (npm install -g @asyncapi/cli)
# ─────────────────────────────────────────────────────────────

# Validate all AsyncAPI specs
validate:
    @echo "Validating AsyncAPI specs..."
    asyncapi validate docs/asyncapi-producer.yaml
    asyncapi validate docs/asyncapi-consumer.yaml
    @echo "✓ All specs valid"

# Open interactive studio for a spec
studio spec:
    asyncapi start studio docs/{{ spec }}.yaml

# Open producer spec in studio
studio-producer:
    asyncapi start studio docs/asyncapi-producer.yaml

# Open consumer spec in studio
studio-consumer:
    asyncapi start studio docs/asyncapi-consumer.yaml

# Generate HTML documentation
docs-html:
    mkdir -p docs/html/producer docs/html/consumer
    asyncapi generate fromTemplate docs/asyncapi-producer.yaml @asyncapi/html-template -o docs/html/producer
    asyncapi generate fromTemplate docs/asyncapi-consumer.yaml @asyncapi/html-template -o docs/html/consumer
    @echo "✓ HTML docs generated in docs/html/"
    @echo "Open docs/html/producer/index.html or docs/html/consumer/index.html"

# Generate markdown documentation
docs-md:
    mkdir -p docs/markdown/producer docs/markdown/consumer
    asyncapi generate fromTemplate docs/asyncapi-producer.yaml @asyncapi/markdown-template -o docs/markdown/producer
    asyncapi generate fromTemplate docs/asyncapi-consumer.yaml @asyncapi/markdown-template -o docs/markdown/consumer
    @echo "✓ Markdown docs generated in docs/markdown/"

# Generate Python Pydantic models from spec
codegen-python:
    mkdir -p generated/python/producer generated/python/consumer
    asyncapi generate models python docs/asyncapi-producer.yaml -o generated/python/producer
    asyncapi generate models python docs/asyncapi-consumer.yaml -o generated/python/consumer
    @echo "✓ Python models generated in generated/python/"

# Generate TypeScript types from spec
codegen-typescript:
    mkdir -p generated/typescript/producer generated/typescript/consumer
    asyncapi generate models typescript docs/asyncapi-producer.yaml -o generated/typescript/producer
    asyncapi generate models typescript docs/asyncapi-consumer.yaml -o generated/typescript/consumer
    @echo "✓ TypeScript types generated in generated/typescript/"

# Show diff between producer and consumer schemas
diff-specs:
    asyncapi diff docs/asyncapi-producer.yaml docs/asyncapi-consumer.yaml

# Bundle specs (resolve all $refs)
bundle:
    mkdir -p docs/bundled
    asyncapi bundle docs/asyncapi-producer.yaml -o docs/bundled/producer.yaml
    asyncapi bundle docs/asyncapi-consumer.yaml -o docs/bundled/consumer.yaml
    @echo "✓ Bundled specs in docs/bundled/"

# ─────────────────────────────────────────────────────────────
# Development
# ─────────────────────────────────────────────────────────────

# Sync producer dependencies
sync-producer:
    cd producer && uv sync

# Sync consumer dependencies
sync-consumer:
    cd consumer && uv sync

# Sync all dependencies
sync: sync-producer sync-consumer

# Run producer locally (outside Docker)
run-producer:
    cd producer && uv run producer run

# Run consumer locally (outside Docker)
run-consumer:
    cd consumer && uv run consumer run

# ─────────────────────────────────────────────────────────────
# Health & Status
# ─────────────────────────────────────────────────────────────

# Check health of all services
health:
    @echo "=== Redpanda ==="
    @docker compose exec redpanda rpk cluster health 2>/dev/null || echo "Not running"
    @echo ""
    @echo "=== LocalStack ==="
    @curl -s http://localhost:4566/_localstack/health | jq . 2>/dev/null || echo "Not running"
    @echo ""
    @echo "=== Services ==="
    @docker compose ps

# Show running services
ps:
    docker compose ps

