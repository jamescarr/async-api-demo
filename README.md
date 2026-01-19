# AsyncAPI Demo: Order Fulfillment System

A demonstration of event-driven architecture using AsyncAPI specifications, FastStream, Redpanda, and AWS SQS (via LocalStack).

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────────┐
│  Order Producer │────▶│  orders.created  │────▶│  Order Fulfillment      │
│   (FastStream)  │     │     (Kafka)      │     │     (FastStream)        │
└─────────────────┘     └──────────────────┘     └──────────┬──────────────┘
                                                           │
                                                           ▼
                        ┌──────────────────┐     ┌─────────────────────────┐
                        │ orders.accepted  │◀────│                         │
                        ├──────────────────┤     │    Publishes Events:    │
                        │ orders.shipped   │◀────│    - OrderAccepted      │
                        ├──────────────────┤     │    - OrderShipped       │
                        │ orders.fulfilled │◀────│    - OrderFulfilled     │
                        └────────┬─────────┘     └─────────────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐     ┌─────────────────────────┐
                        │ Redpanda Connect │────▶│    AWS SQS (LocalStack) │
                        │   (Bridge)       │     │                         │
                        └──────────────────┘     └─────────────────────────┘
```

## Components

| Component | Description | Port |
|-----------|-------------|------|
| Redpanda | Kafka-compatible streaming | 19092 (Kafka), 18081 (Schema Registry) |
| Redpanda Console | Web UI for Redpanda | 8080 |
| LocalStack | AWS SQS emulator | 4566 |
| Order Producer | Generates random orders | - |
| Order Consumer | Processes orders, emits events | - |
| Redpanda Connect | Bridges Kafka to SQS | - |

## Quick Start

```bash
# Start all services
make up

# View logs
make logs

# Stop all services
make down

# View AsyncAPI documentation
make docs
```

## Topics

| Topic | Description | Producer | Consumer |
|-------|-------------|----------|----------|
| `orders.created` | New order events | Order Producer | Order Fulfillment |
| `orders.accepted` | Order validation events | Order Fulfillment | Redpanda Connect |
| `orders.shipped` | Shipping events | Order Fulfillment | Redpanda Connect |
| `orders.fulfilled` | Completion events | Order Fulfillment | Redpanda Connect |

## SQS Queues

| Queue | Description |
|-------|-------------|
| `order-fulfillment-events` | Receives OrderFulfilled events |
| `order-notifications` | Receives OrderAccepted/OrderShipped events |
| `order-fulfillment-events-dlq` | Dead letter queue |

## Avro Schemas

Schemas are defined in the `schemas/` directory:

- `order_created.avsc` - New order events
- `order_accepted.avsc` - Validation events
- `order_shipped.avsc` - Shipping events
- `order_delivered.avsc` - Delivery events

## AsyncAPI Specifications

AsyncAPI documents are in the `docs/` directory:

- `asyncapi-producer.yaml` - Order Producer service API (hand-written)
- `asyncapi-consumer.yaml` - Order Fulfillment service API (hand-written)

### Generate Specs from Code

FastStream can auto-generate AsyncAPI specs directly from your Python code:

```bash
# Generate specs from code
make generate-specs

# Or individually
cd producer && uv run python -m app.asyncapi -o ../docs/generated-producer.yaml
cd consumer && uv run python -m app.asyncapi -o ../docs/generated-consumer.yaml
```

This reads the `@broker.subscriber()` and `broker.publisher()` decorators along with 
Pydantic models to build the spec automatically.

### View Specs

```bash
# Install AsyncAPI CLI
npm install -g @asyncapi/cli

# Interactive studio
make studio-producer
make studio-consumer

# Generate HTML docs
make docs-html
```

## Viewing Messages

### Redpanda Console

Open http://localhost:8080 to see:
- Topics and messages
- Consumer groups
- Schema Registry

### SQS (LocalStack)

```bash
# List queues
aws --endpoint-url=http://localhost:4566 sqs list-queues

# Receive messages from fulfillment queue
aws --endpoint-url=http://localhost:4566 sqs receive-message \
  --queue-url http://localhost:4566/000000000000/order-fulfillment-events \
  --max-number-of-messages 10
```

## Development

### Project Structure

```
asyncapi-demo/
├── docker-compose.yml      # Infrastructure
├── producer/               # Order Producer service
│   ├── app/
│   │   ├── main.py        # FastStream app
│   │   ├── models.py      # Pydantic models
│   │   └── generator.py   # Random order generator
│   ├── Dockerfile
│   └── pyproject.toml     # uv dependencies
├── consumer/               # Order Fulfillment service
│   ├── app/
│   │   ├── main.py        # FastStream app
│   │   └── models.py      # Pydantic models
│   ├── Dockerfile
│   └── pyproject.toml     # uv dependencies
├── connect/                # Redpanda Connect
│   └── pipeline.yaml      # Bridge configuration
├── schemas/                # Avro schemas
│   ├── order_created.avsc
│   ├── order_accepted.avsc
│   ├── order_shipped.avsc
│   └── order_delivered.avsc
├── docs/                   # AsyncAPI specs
│   ├── asyncapi-producer.yaml
│   └── asyncapi-consumer.yaml
└── localstack/            # LocalStack init scripts
    └── init-aws.sh
```

### Rebuilding Services

```bash
# Rebuild all services
make build

# Rebuild specific service
docker compose build producer
docker compose build consumer
```

## License

MIT

