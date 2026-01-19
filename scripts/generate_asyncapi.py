#!/usr/bin/env python3
"""
Generate AsyncAPI specification from Avro schemas.

This script reads Avro schemas from the schemas/ directory (or fetches from
Schema Registry) and generates an AsyncAPI specification.

Usage:
    python scripts/generate_asyncapi.py producer > docs/asyncapi-producer.yaml
    python scripts/generate_asyncapi.py consumer > docs/asyncapi-consumer.yaml
    
    # Fetch from registry and inline:
    python scripts/generate_asyncapi.py producer --registry-url http://localhost:18081 --inline
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

import yaml


def load_avro_schema(path: Path) -> dict:
    """Load an Avro schema from a .avsc file."""
    with open(path) as f:
        return json.load(f)


def fetch_schema_from_registry(registry_url: str, subject: str) -> dict | None:
    """Fetch an Avro schema from the Schema Registry."""
    url = f"{registry_url}/subjects/{subject}/versions/latest/schema"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"Warning: Could not fetch schema from {url}: {e}", file=sys.stderr)
        return None


def avro_to_json_schema(avro_schema: dict) -> dict:
    """Convert Avro schema to JSON Schema (simplified conversion)."""
    avro_type_map = {
        "string": "string",
        "int": "integer",
        "long": "integer",
        "float": "number",
        "double": "number",
        "boolean": "boolean",
        "bytes": "string",
        "null": "null",
    }

    def convert_type(avro_type) -> dict:
        if isinstance(avro_type, str):
            if avro_type in avro_type_map:
                return {"type": avro_type_map[avro_type]}
            return {"type": "string"}  # fallback

        if isinstance(avro_type, dict):
            if avro_type.get("type") == "record":
                return convert_record(avro_type)
            if avro_type.get("type") == "array":
                return {
                    "type": "array",
                    "items": convert_type(avro_type["items"]),
                }
            if avro_type.get("type") == "map":
                return {
                    "type": "object",
                    "additionalProperties": convert_type(avro_type["values"]),
                }
            if avro_type.get("type") == "enum":
                return {
                    "type": "string",
                    "enum": avro_type["symbols"],
                }
            if avro_type.get("logicalType") == "timestamp-millis":
                return {"type": "string", "format": "date-time"}
            if avro_type.get("logicalType") == "date":
                return {"type": "string", "format": "date"}
            if avro_type.get("logicalType") == "decimal":
                return {"type": "string", "description": "Decimal value as string"}
            # Handle bytes with logical type
            if avro_type.get("type") == "bytes":
                return {"type": "string"}
            if avro_type.get("type") == "long":
                if avro_type.get("logicalType"):
                    return {"type": "string", "format": "date-time"}
                return {"type": "integer"}
            if avro_type.get("type") == "int":
                if avro_type.get("logicalType"):
                    return {"type": "string", "format": "date"}
                return {"type": "integer"}

        if isinstance(avro_type, list):
            # Union type - find the non-null type
            non_null = [t for t in avro_type if t != "null"]
            if len(non_null) == 1:
                return convert_type(non_null[0])
            return {"type": "string"}  # fallback

        return {"type": "string"}

    def convert_record(record: dict) -> dict:
        properties = {}
        required = []

        for field in record.get("fields", []):
            field_name = field["name"]
            field_type = field["type"]

            # Check if field is optional (union with null)
            is_optional = isinstance(field_type, list) and "null" in field_type

            if not is_optional and "default" not in field:
                required.append(field_name)

            prop = convert_type(field_type)
            if field.get("doc"):
                prop["description"] = field["doc"]
            if "default" in field and field["default"] is not None:
                prop["default"] = field["default"]

            properties[field_name] = prop

        result = {
            "type": "object",
            "properties": properties,
        }
        if required:
            result["required"] = required
        if record.get("doc"):
            result["description"] = record["doc"]

        return result

    return convert_record(avro_schema)


def generate_producer_spec(
    schemas_dir: Path,
    registry_url: str = "http://redpanda:8081",
    inline: bool = False,
) -> dict:
    """Generate AsyncAPI spec for the producer service.
    
    Args:
        schemas_dir: Path to the schemas directory
        registry_url: Schema Registry URL for references
        inline: If True, fetch and inline the schema from registry.
                If False, use $ref to registry (use `asyncapi bundle` to resolve)
    """
    # Load schema for doc extraction
    order_created = load_avro_schema(schemas_dir / "order_created.avsc")
    
    # Build payload - either inline the Avro schema or reference the registry
    if inline:
        # Fetch from registry and inline
        fetched_schema = fetch_schema_from_registry(registry_url, "orders.created-value")
        if fetched_schema:
            order_created = fetched_schema
        else:
            print("Warning: Could not fetch from registry, using local file", file=sys.stderr)
        
        payload = {
            "schemaFormat": "application/vnd.apache.avro+json;version=1.9.0",
            "schema": order_created,
        }
    else:
        # Reference the schema registry URL directly
        # Use `asyncapi bundle` to resolve $ref if needed
        payload = {
            "schemaFormat": "application/vnd.apache.avro+json;version=1.9.0",
            "schema": {
                "$ref": f"{registry_url}/subjects/orders.created-value/versions/latest/schema"
            },
        }

    return {
        "asyncapi": "3.0.0",
        "info": {
            "title": "Order Producer Service",
            "version": "1.0.0",
            "description": f"""## Order Producer Service

This service generates order events and publishes them to Kafka.

### Events Published

- **OrderCreated**: Emitted when a new order is placed

### Schema Registry

Events use Avro schemas registered in the Redpanda Schema Registry: `{registry_url}`
""",
        },
        "defaultContentType": "application/vnd.apache.avro+json",
        "servers": {
            "development": {
                "host": "localhost:19092",
                "protocol": "kafka",
                "description": "Local Redpanda broker",
            },
        },
        "channels": {
            "orders.created": {
                "address": "orders.created",
                "description": "Topic for newly created order events",
                "messages": {
                    "OrderCreated": {"$ref": "#/components/messages/OrderCreated"},
                },
            },
        },
        "operations": {
            "publishOrderCreated": {
                "action": "send",
                "channel": {"$ref": "#/channels/orders.created"},
                "summary": "Publish a new order event",
                "messages": [{"$ref": "#/channels/orders.created/messages/OrderCreated"}],
            },
        },
        "components": {
            "messages": {
                "OrderCreated": {
                    "name": "OrderCreated",
                    "title": "Order Created Event",
                    "summary": order_created.get("doc", "Event emitted when a new order is placed"),
                    "contentType": "application/vnd.apache.avro+json",
                    "payload": payload,
                },
            },
        },
    }


def generate_consumer_spec(schemas_dir: Path) -> dict:
    """Generate AsyncAPI spec for the consumer service."""
    order_created = load_avro_schema(schemas_dir / "order_created.avsc")
    order_created_json = avro_to_json_schema(order_created)

    return {
        "asyncapi": "3.0.0",
        "info": {
            "title": "Order Fulfillment Service",
            "version": "1.0.0",
            "description": """## Order Fulfillment Service

This service consumes order events from SQS (bridged from Kafka via Redpanda Connect).

### Events Consumed

- **OrderCreated**: Triggers the fulfillment process

### Processing Pipeline

```
Kafka → Redpanda Connect → SQS → Consumer
```
""",
        },
        "defaultContentType": "application/json",
        "servers": {
            "localstack": {
                "host": "localstack:4566",
                "protocol": "sqs",
                "description": "LocalStack SQS endpoint",
            },
        },
        "channels": {
            "order-events": {
                "address": "order-events",
                "description": "SQS queue receiving order events bridged from Kafka",
                "messages": {
                    "OrderCreated": {"$ref": "#/components/messages/OrderCreated"},
                },
            },
        },
        "operations": {
            "receiveOrderCreated": {
                "action": "receive",
                "channel": {"$ref": "#/channels/order-events"},
                "summary": "Receive order created events from SQS",
                "messages": [{"$ref": "#/channels/order-events/messages/OrderCreated"}],
            },
        },
        "components": {
            "messages": {
                "OrderCreated": {
                    "name": "OrderCreated",
                    "title": "Order Created Event",
                    "summary": order_created.get("doc", "Event emitted when a new order is placed"),
                    "description": f"Generated from Avro schema: schemas/order_created.avsc\nNamespace: {order_created.get('namespace', 'N/A')}",
                    "contentType": "application/json",
                    "payload": {"$ref": "#/components/schemas/OrderCreated"},
                },
            },
            "schemas": {
                "OrderCreated": order_created_json,
            },
        },
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate AsyncAPI specs from Avro schemas")
    parser.add_argument("service", choices=["producer", "consumer"], help="Service to generate spec for")
    parser.add_argument(
        "--registry-url",
        default="http://redpanda:8081",
        help="Schema Registry URL (default: http://redpanda:8081 for Docker)",
    )
    parser.add_argument(
        "--inline",
        action="store_true",
        help="Fetch and inline schemas from registry instead of using $ref",
    )
    args = parser.parse_args()

    schemas_dir = Path(__file__).parent.parent / "schemas"

    if args.service == "producer":
        spec = generate_producer_spec(schemas_dir, args.registry_url, args.inline)
    elif args.service == "consumer":
        spec = generate_consumer_spec(schemas_dir)

    print(yaml.dump(spec, default_flow_style=False, sort_keys=False, allow_unicode=True))


if __name__ == "__main__":
    main()

