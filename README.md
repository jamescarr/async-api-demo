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
# Install just (command runner)
# macOS: brew install just
# Linux: cargo install just

# Start all services
just up

# View logs
just logs

# Stop all services
just down

# See all available commands
just
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

AsyncAPI documents are in the `docs/` directory and are auto-generated from code.

### Generate Specs from Code

FastStream auto-generates AsyncAPI specs from your Python code:

```bash
# Generate all specs
just generate-specs

# Or individually
just generate-producer-spec
just generate-consumer-spec
```

This reads the `@broker.subscriber()` and `broker.publisher()` decorators along with 
Pydantic models to build the spec automatically.

### View Specs

```bash
# Install AsyncAPI CLI
npm install -g @asyncapi/cli

# Interactive studio
just studio-producer
just studio-consumer

# Generate HTML docs
just docs-html

# Validate specs
just validate
```

## Viewing Messages

### Redpanda Console

Open http://localhost:8080 to see:
- Topics and messages
- Consumer groups
- Schema Registry

### Redpanda CLI

```bash
# List topics
just topics

# Consume from a topic
just consume orders.created

# View consumer groups
just groups
```

### SQS (LocalStack)

```bash
# List queues
just sqs-queues

# Receive messages
just sqs-messages
```

## Development

### CLI Commands

Each service has a click-based CLI:

```bash
# Producer
cd producer && uv run producer --help
cd producer && uv run producer run          # Run the service
cd producer && uv run producer asyncapi     # Generate AsyncAPI spec

# Consumer  
cd consumer && uv run consumer --help
cd consumer && uv run consumer run          # Run the service
cd consumer && uv run consumer asyncapi     # Generate AsyncAPI spec
```

### Project Structure

```
asyncapi-demo/
├── justfile                # Command runner
├── docker-compose.yml      # Infrastructure
├── producer/               # Order Producer service
│   ├── app/
│   │   ├── main.py        # FastStream app
│   │   ├── models.py      # Pydantic models
│   │   ├── generator.py   # Random order generator
│   │   └── cli.py         # Click CLI
│   ├── Dockerfile
│   └── pyproject.toml     # uv dependencies
├── consumer/               # Order Fulfillment service
│   ├── app/
│   │   ├── main.py        # FastStream app
│   │   ├── models.py      # Pydantic models
│   │   └── cli.py         # Click CLI
│   ├── Dockerfile
│   └── pyproject.toml     # uv dependencies
├── connect/                # Redpanda Connect
│   └── pipeline.yaml      # Bridge configuration
├── schemas/                # Avro schemas
│   ├── order_created.avsc
│   ├── order_accepted.avsc
│   ├── order_shipped.avsc
│   └── order_delivered.avsc
├── docs/                   # AsyncAPI specs (generated)
│   ├── asyncapi-producer.yaml
│   └── asyncapi-consumer.yaml
└── localstack/            # LocalStack init scripts
    └── init-aws.sh
```

### Rebuilding Services

```bash
# Rebuild all services
just build

# Rebuild and restart
just rebuild
```

### Health Check

```bash
just health
```

## License

MIT
