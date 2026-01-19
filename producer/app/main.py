"""
Order Producer Service

A FastStream-based service that generates random orders and publishes them
to a Kafka topic. This demonstrates how to:

1. Define message schemas with Pydantic
2. Publish events to Kafka
3. Auto-generate AsyncAPI documentation
"""
import asyncio
import os

import structlog
from faststream import FastStream
from faststream.kafka import KafkaBroker
from faststream.specification import AsyncAPI

from .models import OrderCreated
from .generator import generate_order

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
ORDERS_TOPIC = "orders.created"
PUBLISH_INTERVAL_SECONDS = int(os.getenv("PUBLISH_INTERVAL_SECONDS", "5"))

# Create Kafka broker
broker = KafkaBroker(KAFKA_BOOTSTRAP_SERVERS)

# AsyncAPI specification metadata
spec = AsyncAPI(
    title="Order Producer Service",
    version="1.0.0",
    description="""
## Order Producer Service

This service generates order events and publishes them to Kafka.
It simulates an e-commerce order intake system.

### Events Published

- **OrderCreated**: Emitted when a new order is placed

### Architecture

```
[Order Producer] --> [orders.created topic] --> [Order Consumer]
                                             |
                                             --> [Redpanda Connect] --> [SQS]
```
""",
)

# Create FastStream application
app = FastStream(broker, specification=spec)

# Publisher for order events - typed with Pydantic model for AsyncAPI generation
publisher = broker.publisher(
    ORDERS_TOPIC,
    title="OrderCreated",
    description="Publishes new order events to the orders.created topic",
    schema=OrderCreated,
)


@app.after_startup
async def startup():
    """Initialize and start the order generation loop."""
    logger.info(
        "order_producer_started",
        kafka_servers=KAFKA_BOOTSTRAP_SERVERS,
        topic=ORDERS_TOPIC,
        interval_seconds=PUBLISH_INTERVAL_SECONDS,
    )
    # Start the order generation loop as a background task
    asyncio.create_task(generate_orders_loop())


async def generate_orders_loop():
    """Continuously generate and publish random orders."""
    await asyncio.sleep(5)  # Wait for broker to be ready
    
    while True:
        try:
            order = generate_order()
            
            # Publish the order event
            await publisher.publish(
                order.model_dump_json(),
                key=order.customer_id.encode(),  # Use customer ID as partition key
                headers={
                    "event_type": "OrderCreated",
                    "correlation_id": order.order_id,
                    "source": "order-producer",
                },
            )
            
            logger.info(
                "order_published",
                order_id=order.order_id,
                customer_id=order.customer_id,
                total_amount=str(order.total_amount),
                item_count=len(order.items),
            )
            
        except Exception as e:
            logger.error("order_publish_failed", error=str(e))
        
        await asyncio.sleep(PUBLISH_INTERVAL_SECONDS)

