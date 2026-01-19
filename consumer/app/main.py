"""
Order Fulfillment Consumer Service

A FastStream-based service that consumes order events and processes them
through the fulfillment pipeline. This demonstrates how to:

1. Subscribe to Kafka topics with consumer groups
2. Process events and publish downstream events
3. Auto-generate AsyncAPI documentation
"""
import asyncio
import json
import os
import random
from datetime import datetime, timedelta

import structlog
from faststream import FastStream
from faststream.kafka import KafkaBroker
from faststream.kafka.annotations import KafkaMessage
from faststream.specification import AsyncAPI

from .models import (
    OrderCreated,
    OrderAccepted,
    OrderShipped,
    OrderFulfilled,
    Carrier,
)

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

# Topics
ORDERS_CREATED_TOPIC = "orders.created"
ORDERS_ACCEPTED_TOPIC = "orders.accepted"
ORDERS_SHIPPED_TOPIC = "orders.shipped"
ORDERS_FULFILLED_TOPIC = "orders.fulfilled"

# Simulated warehouses
WAREHOUSES = ["wh_east_01", "wh_west_01", "wh_central_01"]

# Create Kafka broker
broker = KafkaBroker(KAFKA_BOOTSTRAP_SERVERS)

# AsyncAPI specification metadata
spec = AsyncAPI(
    title="Order Fulfillment Service",
    version="1.0.0",
    description="""
## Order Fulfillment Service

This service processes orders through the fulfillment pipeline.
It consumes order creation events and produces fulfillment lifecycle events.

### Events Consumed

- **OrderCreated**: Triggers the fulfillment process

### Events Published

- **OrderAccepted**: Order validated and queued for fulfillment
- **OrderShipped**: Order has been shipped with tracking info
- **OrderFulfilled**: Terminal event, order process complete

### Processing Pipeline

```
OrderCreated --> Validate --> OrderAccepted --> Ship --> OrderShipped --> OrderFulfilled
```
""",
)

# Create FastStream application
app = FastStream(broker, specification=spec)

# Publishers - typed with Pydantic models for AsyncAPI generation
accepted_publisher = broker.publisher(
    ORDERS_ACCEPTED_TOPIC,
    title="OrderAccepted",
    description="Publishes events when orders are validated and accepted",
    schema=OrderAccepted,
)

shipped_publisher = broker.publisher(
    ORDERS_SHIPPED_TOPIC,
    title="OrderShipped",
    description="Publishes events when orders are shipped",
    schema=OrderShipped,
)

fulfilled_publisher = broker.publisher(
    ORDERS_FULFILLED_TOPIC,
    title="OrderFulfilled",
    description="Publishes events when orders complete fulfillment",
    schema=OrderFulfilled,
)


def generate_tracking_number(carrier: Carrier) -> str:
    """Generate a realistic tracking number for the carrier."""
    if carrier == Carrier.UPS:
        return f"1Z{random.randint(100, 999)}AA{random.randint(10000000, 99999999)}"
    elif carrier == Carrier.FEDEX:
        return f"{random.randint(1000000000, 9999999999)}"
    elif carrier == Carrier.USPS:
        return f"94{random.randint(10000000000000000, 99999999999999999)}"
    else:  # DHL
        return f"{random.randint(1000000000, 9999999999)}"


@broker.subscriber(
    ORDERS_CREATED_TOPIC,
    group_id="order-fulfillment-service",
    title="OrderCreated",
    description="Consumes new order events and initiates fulfillment",
)
async def handle_order_created(body: str, msg: KafkaMessage):
    """
    Process a new order and move it through the fulfillment pipeline.
    
    This simulates:
    1. Order validation and acceptance
    2. Warehouse assignment
    3. Shipping
    4. Fulfillment completion
    """
    try:
        order_data = json.loads(body)
        order = OrderCreated(**order_data)
        
        correlation_id = order.order_id
        
        logger.info(
            "order_received",
            order_id=order.order_id,
            customer_id=order.customer_id,
            total_amount=str(order.total_amount),
            item_count=len(order.items),
        )
        
        # Step 1: Validate and accept the order
        warehouse_id = random.choice(WAREHOUSES)
        estimated_ship_date = (datetime.utcnow() + timedelta(days=random.randint(1, 3))).date()
        
        accepted_event = OrderAccepted(
            order_id=order.order_id,
            customer_id=order.customer_id,
            estimated_ship_date=estimated_ship_date,
            warehouse_id=warehouse_id,
            correlation_id=correlation_id,
        )
        
        await accepted_publisher.publish(
            accepted_event.model_dump_json(),
            key=order.customer_id.encode(),
            headers={
                "event_type": "OrderAccepted",
                "correlation_id": correlation_id,
                "source": "order-fulfillment",
            },
        )
        
        logger.info(
            "order_accepted",
            order_id=order.order_id,
            warehouse_id=warehouse_id,
            estimated_ship_date=str(estimated_ship_date),
        )
        
        # Simulate processing delay
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Step 2: Ship the order
        carrier = random.choice(list(Carrier))
        tracking_number = generate_tracking_number(carrier)
        estimated_delivery = (datetime.utcnow() + timedelta(days=random.randint(2, 5))).date()
        
        shipped_event = OrderShipped(
            order_id=order.order_id,
            customer_id=order.customer_id,
            tracking_number=tracking_number,
            carrier=carrier,
            estimated_delivery_date=estimated_delivery,
            warehouse_id=warehouse_id,
            correlation_id=correlation_id,
        )
        
        await shipped_publisher.publish(
            shipped_event.model_dump_json(),
            key=order.customer_id.encode(),
            headers={
                "event_type": "OrderShipped",
                "correlation_id": correlation_id,
                "source": "order-fulfillment",
            },
        )
        
        logger.info(
            "order_shipped",
            order_id=order.order_id,
            carrier=carrier.value,
            tracking_number=tracking_number,
        )
        
        # Step 3: Mark as fulfilled
        fulfilled_event = OrderFulfilled(
            order_id=order.order_id,
            customer_id=order.customer_id,
            tracking_number=tracking_number,
            carrier=carrier,
            total_amount=order.total_amount,
            correlation_id=correlation_id,
        )
        
        await fulfilled_publisher.publish(
            fulfilled_event.model_dump_json(),
            key=order.customer_id.encode(),
            headers={
                "event_type": "OrderFulfilled",
                "correlation_id": correlation_id,
                "source": "order-fulfillment",
            },
        )
        
        logger.info(
            "order_fulfilled",
            order_id=order.order_id,
            customer_id=order.customer_id,
        )
        
    except Exception as e:
        logger.error(
            "order_processing_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise


@app.after_startup
async def startup():
    """Log service startup."""
    logger.info(
        "order_fulfillment_service_started",
        kafka_servers=KAFKA_BOOTSTRAP_SERVERS,
        consumer_group="order-fulfillment-service",
        subscribed_topics=[ORDERS_CREATED_TOPIC],
        publish_topics=[ORDERS_ACCEPTED_TOPIC, ORDERS_SHIPPED_TOPIC, ORDERS_FULFILLED_TOPIC],
    )

