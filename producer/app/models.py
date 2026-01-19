"""
Pydantic models for order events.

These models are used by FastStream for serialization and automatically
generate AsyncAPI documentation.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class Address(BaseModel):
    """Shipping or billing address."""
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"


class OrderItem(BaseModel):
    """Individual item in an order."""
    product_id: str
    product_name: str
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(decimal_places=2)


class OrderCreated(BaseModel):
    """
    Event published when a new order is created.
    
    This is the initiating event in the order fulfillment saga.
    It triggers downstream processes like inventory reservation,
    payment processing, and shipping preparation.
    """
    order_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    customer_email: str
    items: list[OrderItem]
    total_amount: Decimal = Field(decimal_places=2)
    shipping_address: Address
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, str] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "order_id": "ord_12345",
                    "customer_id": "cust_67890",
                    "customer_email": "customer@example.com",
                    "items": [
                        {
                            "product_id": "prod_001",
                            "product_name": "Wireless Headphones",
                            "quantity": 1,
                            "unit_price": "79.99"
                        }
                    ],
                    "total_amount": "79.99",
                    "shipping_address": {
                        "street": "123 Main St",
                        "city": "Austin",
                        "state": "TX",
                        "zip_code": "78701",
                        "country": "USA"
                    },
                    "metadata": {"source": "web", "campaign": "holiday_sale"}
                }
            ]
        }

