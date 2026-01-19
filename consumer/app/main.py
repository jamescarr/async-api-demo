"""
Order Fulfillment Consumer Service

An aiobotocore-based service that consumes order events from SQS
and processes them through the fulfillment pipeline.
"""
import asyncio
import json
import os
import random
from datetime import datetime, timedelta

import structlog
from aiobotocore.session import get_session
from pydantic import ValidationError

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

# Configuration
SQS_ENDPOINT = os.getenv("SQS_ENDPOINT", "http://localhost:4566")
SQS_QUEUE_NAME = os.getenv("SQS_QUEUE_NAME", "order-events")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")

# Simulated warehouses
WAREHOUSES = ["wh_east_01", "wh_west_01", "wh_central_01"]


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


async def process_order(order: OrderCreated) -> None:
    """
    Process a new order through the fulfillment pipeline.
    
    Simulates:
    1. Order validation and acceptance
    2. Warehouse assignment
    3. Shipping
    4. Fulfillment completion
    """
    logger.info(
        "order_received",
        order_id=order.order_id,
        customer_id=order.customer_id,
        total_amount=str(order.total_amount),
        item_count=len(order.items),
    )

    # Step 1: Accept the order
    warehouse_id = random.choice(WAREHOUSES)
    estimated_ship_date = (datetime.utcnow() + timedelta(days=random.randint(1, 3))).date()

    accepted = OrderAccepted(
        order_id=order.order_id,
        customer_id=order.customer_id,
        estimated_ship_date=estimated_ship_date,
        warehouse_id=warehouse_id,
    )

    logger.info(
        "order_accepted",
        order_id=order.order_id,
        warehouse_id=warehouse_id,
        estimated_ship_date=str(estimated_ship_date),
    )

    # Step 2: Ship the order
    carrier = random.choice(list(Carrier))
    tracking_number = generate_tracking_number(carrier)
    estimated_delivery = (datetime.utcnow() + timedelta(days=random.randint(2, 5))).date()

    shipped = OrderShipped(
        order_id=order.order_id,
        customer_id=order.customer_id,
        tracking_number=tracking_number,
        carrier=carrier,
        estimated_delivery_date=estimated_delivery,
        warehouse_id=warehouse_id,
    )

    logger.info(
        "order_shipped",
        order_id=order.order_id,
        carrier=carrier.value,
        tracking_number=tracking_number,
    )

    # Step 3: Mark as fulfilled
    fulfilled = OrderFulfilled(
        order_id=order.order_id,
        customer_id=order.customer_id,
        tracking_number=tracking_number,
        carrier=carrier,
        total_amount=order.total_amount,
    )

    logger.info(
        "order_fulfilled",
        order_id=order.order_id,
        customer_id=order.customer_id,
    )


async def handle_message(body: str) -> None:
    """Parse and process an SQS message."""
    try:
        data = json.loads(body)
        order = OrderCreated(**data)
        await process_order(order)
    except json.JSONDecodeError as e:
        logger.error("invalid_json", error=str(e), body=body[:200])
        raise
    except ValidationError as e:
        logger.error("validation_error", error=str(e), body=body[:200])
        raise


async def consume_messages() -> None:
    """Poll SQS and process messages."""
    session = get_session()

    async with session.create_client(
        "sqs",
        region_name=AWS_REGION,
        endpoint_url=SQS_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    ) as client:
        # Get queue URL
        response = await client.get_queue_url(QueueName=SQS_QUEUE_NAME)
        queue_url = response["QueueUrl"]

        logger.info(
            "consumer_started",
            queue_name=SQS_QUEUE_NAME,
            queue_url=queue_url,
            endpoint=SQS_ENDPOINT,
        )

        while True:
            try:
                response = await client.receive_message(
                    QueueUrl=queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=20,
                )
                messages = response.get("Messages", [])

                for message in messages:
                    try:
                        await handle_message(message["Body"])
                        await client.delete_message(
                            QueueUrl=queue_url,
                            ReceiptHandle=message["ReceiptHandle"],
                        )
                    except Exception as e:
                        logger.error(
                            "message_processing_failed",
                            message_id=message.get("MessageId"),
                            error=str(e),
                        )

            except Exception as e:
                logger.error("poll_error", error=str(e), error_type=type(e).__name__)
                await asyncio.sleep(5)


async def run() -> None:
    """Entry point for the consumer."""
    await consume_messages()
