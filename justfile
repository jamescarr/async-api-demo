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

# Check SQS messages
sqs-messages:
    @echo "=== Order Events Queue ==="
    aws --endpoint-url=http://localhost:4566 sqs receive-message \
        --queue-url http://localhost:4566/000000000000/order-events \
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
# Avro Schemas
# ─────────────────────────────────────────────────────────────

# List all Avro schemas
list-schemas:
    @echo "=== Avro Schemas ==="
    @ls -la schemas/*.avsc

# Validate Avro schemas (requires avro-tools or python fastavro)
validate-schemas:
    @echo "Validating Avro schemas..."
    @for f in schemas/*.avsc; do \
        echo "  Checking $$f..."; \
        python3 -c "import json; json.load(open('$$f'))" && echo "    ✓ Valid JSON"; \
    done
    @echo "✓ All schemas are valid JSON"

# Register schema with Redpanda Schema Registry
register-schema subject schema:
    @echo "Registering {{ schema }} as {{ subject }}..."
    curl -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
        --data "{\"schema\": $(cat schemas/{{ schema }} | jq -c . | jq -Rs .)}" \
        http://localhost:18081/subjects/{{ subject }}/versions
    @echo ""

# Register all schemas with default subjects
register-all-schemas:
    @echo "Registering schemas with Schema Registry..."
    just register-schema orders.created-value order_created.avsc
    just register-schema orders.accepted-value order_accepted.avsc
    just register-schema orders.shipped-value order_shipped.avsc
    just register-schema orders.delivered-value order_delivered.avsc
    @echo "✓ All schemas registered"

# Schema Registry URL (use localhost for fetching schemas)
registry_url := "http://localhost:18081"

# Generate AsyncAPI specs with inlined Avro schemas (fetched from registry)
generate-specs:
    @echo "Generating AsyncAPI specs from Avro schemas..."
    @echo "  Fetching from Schema Registry: {{ registry_url }}"
    uv run --with pyyaml python scripts/generate_asyncapi.py producer --registry-url {{ registry_url }} --inline > docs/asyncapi-producer.yaml
    uv run --with pyyaml python scripts/generate_asyncapi.py consumer > docs/asyncapi-consumer.yaml
    @echo "✓ Generated docs/asyncapi-producer.yaml (Avro schema inlined)"
    @echo "✓ Generated docs/asyncapi-consumer.yaml (JSON Schema)"

# Generate AsyncAPI specs with $ref to Schema Registry (not inlined)
generate-specs-ref:
    @echo "Generating AsyncAPI specs with registry references..."
    uv run --with pyyaml python scripts/generate_asyncapi.py producer --registry-url http://redpanda:8081 > docs/asyncapi-producer.yaml
    uv run --with pyyaml python scripts/generate_asyncapi.py consumer > docs/asyncapi-consumer.yaml
    @echo "✓ Generated docs/asyncapi-producer.yaml (refs http://redpanda:8081)"
    @echo "✓ Generated docs/asyncapi-consumer.yaml"

# List schemas in registry
registry-schemas:
    @echo "=== Schema Registry Subjects ==="
    curl -s http://localhost:18081/subjects | jq .

# Get schema by subject
registry-get subject:
    curl -s http://localhost:18081/subjects/{{ subject }}/versions/latest | jq .

# ─────────────────────────────────────────────────────────────
# AsyncAPI CLI Tools (npm install -g @asyncapi/cli)
# ─────────────────────────────────────────────────────────────

# Validate AsyncAPI specs
validate:
    @echo "Validating AsyncAPI specs..."
    asyncapi validate docs/asyncapi-producer.yaml
    asyncapi validate docs/asyncapi-consumer.yaml
    @echo "✓ All specs valid"

# Open producer spec in AsyncAPI Studio
studio-producer:
    asyncapi start studio docs/asyncapi-producer.yaml

# Open consumer spec in AsyncAPI Studio
studio-consumer:
    asyncapi start studio docs/asyncapi-consumer.yaml

# Open both specs side-by-side (requires two terminals)
studio:
    @echo "Run these in separate terminals:"
    @echo "  just studio-producer"
    @echo "  just studio-consumer"

# Generate HTML documentation
docs-html:
    mkdir -p docs/html/producer docs/html/consumer
    asyncapi generate fromTemplate docs/asyncapi-producer.yaml @asyncapi/html-template -o docs/html/producer
    asyncapi generate fromTemplate docs/asyncapi-consumer.yaml @asyncapi/html-template -o docs/html/consumer
    @echo "✓ HTML docs generated in docs/html/"

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
    cd producer && uv run python -m app.cli run

# Run consumer locally (outside Docker)
run-consumer:
    cd consumer && uv run python -m app.cli run

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

