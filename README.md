# AsyncAPI Demo: Order Fulfillment System

A demonstration of event-driven architecture using AsyncAPI specifications, FastStream, Redpanda, Redpanda Connect, and AWS SQS (via LocalStack).

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Order Producer │────▶│  orders.created  │────▶│ Redpanda Connect │────▶│     SQS     │
│   (FastStream)  │     │     (Kafka)      │     │    (Bridge)      │     │   Queue     │
└─────────────────┘     └──────────────────┘     └──────────────────┘     └──────┬──────┘
                                                                                  │
                                                                                  ▼
                                                                          ┌─────────────┐
                                                                          │  Consumer   │
                                                                          │   (SQS)     │
                                                                          └─────────────┘
```

**Flow:**
1. Producer generates order events and publishes to Kafka (`orders.created` topic)
2. Redpanda Connect bridges events from Kafka to SQS
3. Consumer polls SQS queue and processes orders

## Components

| Component | Description | Port |
|-----------|-------------|------|
| Redpanda | Kafka-compatible streaming | 19092 (Kafka), 18081 (Schema Registry) |
| Redpanda Console | Web UI for Redpanda | 8080 |
| Redpanda Connect | Bridges Kafka → SQS | - |
| LocalStack | AWS SQS emulator | 4566 |
| Order Producer | Generates random orders (FastStream) | - |
| Order Consumer | Processes orders from SQS | - |

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

## Topics & Queues

**Kafka Topics:**
| Topic | Description | Producer |
|-------|-------------|----------|
| `orders.created` | New order events | Order Producer |

**SQS Queues:**
| Queue | Description |
|-------|-------------|
| `order-events` | Order events (bridged from Kafka) |
| `order-events-dlq` | Dead letter queue |

## AsyncAPI Specification

The producer's AsyncAPI spec is auto-generated from code:

```bash
# Generate spec
just generate-spec

# Validate spec
just validate

# Open in interactive studio
just studio

# Generate HTML docs
just docs-html
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

```bash
# Producer
cd producer && uv run python -m app.cli --help
cd producer && uv run python -m app.cli run

# Consumer
cd consumer && uv run python -m app.cli --help
cd consumer && uv run python -m app.cli run
```

### Project Structure

```
asyncapi-demo/
├── justfile                # Command runner
├── docker-compose.yml      # Infrastructure
├── producer/               # Order Producer service (FastStream + Kafka)
│   ├── app/
│   │   ├── main.py        # FastStream app
│   │   ├── models.py      # Pydantic models
│   │   ├── generator.py   # Random order generator
│   │   └── cli.py         # Click CLI
│   ├── Dockerfile
│   └── pyproject.toml
├── consumer/               # Order Consumer service (SQS)
│   ├── app/
│   │   ├── main.py        # SQS polling consumer
│   │   └── cli.py         # Click CLI
│   ├── Dockerfile
│   └── pyproject.toml
├── connect/                # Redpanda Connect
│   └── pipeline.yaml      # Kafka → SQS bridge config
├── docs/                   # AsyncAPI specs (generated)
│   └── asyncapi-producer.yaml
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
