.PHONY: up down logs build clean docs producer-logs consumer-logs connect-logs sqs-messages

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

# Build all services
build:
	docker compose build

# Clean up volumes
clean:
	docker compose down -v
	docker system prune -f

# View producer logs
producer-logs:
	docker compose logs -f producer

# View consumer logs
consumer-logs:
	docker compose logs -f consumer

# View Redpanda Connect logs
connect-logs:
	docker compose logs -f connect

# Check SQS messages
sqs-messages:
	@echo "=== Order Fulfillment Events Queue ==="
	aws --endpoint-url=http://localhost:4566 sqs receive-message \
		--queue-url http://localhost:4566/000000000000/order-fulfillment-events \
		--max-number-of-messages 5 2>/dev/null || echo "No messages"
	@echo "\n=== Order Notifications Queue ==="
	aws --endpoint-url=http://localhost:4566 sqs receive-message \
		--queue-url http://localhost:4566/000000000000/order-notifications \
		--max-number-of-messages 5 2>/dev/null || echo "No messages"

# List SQS queues
sqs-queues:
	aws --endpoint-url=http://localhost:4566 sqs list-queues

# === AsyncAPI Tools ===
# Install: npm install -g @asyncapi/cli

# Validate AsyncAPI specs
validate:
	@echo "Validating AsyncAPI specs..."
	asyncapi validate docs/asyncapi-producer.yaml
	asyncapi validate docs/asyncapi-consumer.yaml
	@echo "✓ All specs valid"

# Open interactive studio for producer spec
studio-producer:
	asyncapi start studio docs/asyncapi-producer.yaml

# Open interactive studio for consumer spec  
studio-consumer:
	asyncapi start studio docs/asyncapi-consumer.yaml

# Generate HTML documentation
docs-html:
	@mkdir -p docs/html/producer docs/html/consumer
	asyncapi generate fromTemplate docs/asyncapi-producer.yaml @asyncapi/html-template -o docs/html/producer
	asyncapi generate fromTemplate docs/asyncapi-consumer.yaml @asyncapi/html-template -o docs/html/consumer
	@echo "✓ HTML docs generated in docs/html/"
	@echo "Open docs/html/producer/index.html or docs/html/consumer/index.html"

# Generate markdown documentation
docs-md:
	@mkdir -p docs/markdown
	asyncapi generate fromTemplate docs/asyncapi-producer.yaml @asyncapi/markdown-template -o docs/markdown/producer
	asyncapi generate fromTemplate docs/asyncapi-consumer.yaml @asyncapi/markdown-template -o docs/markdown/consumer
	@echo "✓ Markdown docs generated in docs/markdown/"

# Generate Python Pydantic models from spec
codegen-python:
	@mkdir -p generated/python
	asyncapi generate models python docs/asyncapi-producer.yaml -o generated/python/producer
	asyncapi generate models python docs/asyncapi-consumer.yaml -o generated/python/consumer
	@echo "✓ Python models generated in generated/python/"

# Generate TypeScript types from spec
codegen-typescript:
	@mkdir -p generated/typescript
	asyncapi generate models typescript docs/asyncapi-producer.yaml -o generated/typescript/producer
	asyncapi generate models typescript docs/asyncapi-consumer.yaml -o generated/typescript/consumer
	@echo "✓ TypeScript types generated in generated/typescript/"

# Show diff between producer and consumer schemas
diff-specs:
	asyncapi diff docs/asyncapi-producer.yaml docs/asyncapi-consumer.yaml

# Bundle specs (resolve all $refs)
bundle:
	@mkdir -p docs/bundled
	asyncapi bundle docs/asyncapi-producer.yaml -o docs/bundled/producer.yaml
	asyncapi bundle docs/asyncapi-consumer.yaml -o docs/bundled/consumer.yaml
	@echo "✓ Bundled specs in docs/bundled/"

# === Generate AsyncAPI from Code ===

# Generate spec from producer code
generate-producer-spec:
	cd producer && uv run producer asyncapi --yaml -o ../docs/asyncapi-producer.yaml

# Generate spec from consumer code
generate-consumer-spec:
	cd consumer && uv run consumer asyncapi --yaml -o ../docs/asyncapi-consumer.yaml

# Generate all specs from code
generate-specs: generate-producer-spec generate-consumer-spec
	@echo "✓ All specs generated from code"

# Serve docs locally (interactive viewer)
serve-producer-docs:
	cd producer && uv run faststream docs serve app.main:app

serve-consumer-docs:
	cd consumer && uv run faststream docs serve app.main:app

# Check Redpanda topics
topics:
	docker compose exec redpanda rpk topic list

# Describe a topic
topic-describe:
	@read -p "Topic name: " topic; \
	docker compose exec redpanda rpk topic describe $$topic

# Consume messages from a topic (interactive)
consume:
	@read -p "Topic name: " topic; \
	docker compose exec redpanda rpk topic consume $$topic

# Check consumer groups
groups:
	docker compose exec redpanda rpk group list

# Health check
health:
	@echo "=== Redpanda ==="
	@docker compose exec redpanda rpk cluster health 2>/dev/null || echo "Not running"
	@echo "\n=== LocalStack ==="
	@curl -s http://localhost:4566/_localstack/health | jq . 2>/dev/null || echo "Not running"
	@echo "\n=== Services ==="
	@docker compose ps

