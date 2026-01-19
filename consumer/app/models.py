"""
Pydantic models for order fulfillment events.

These models are used by FastStream for serialization and automatically
generate AsyncAPI documentation.
"""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


# Inbound event models (consumed)

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
    Event consumed when a new order is created.
    
    This is the initiating event that triggers the fulfillment process.
    """
    order_id: str
    customer_id: str
    customer_email: str
    items: list[OrderItem]
    total_amount: Decimal = Field(decimal_places=2)
    shipping_address: Address
    created_at: datetime
    metadata: dict[str, str] = Field(default_factory=dict)


# Outbound event models (published)

class Carrier(str, Enum):
    """Shipping carrier options."""
    FEDEX = "FEDEX"
    UPS = "UPS"
    USPS = "USPS"
    DHL = "DHL"


class OrderAccepted(BaseModel):
    """
    Event published when an order has been validated and accepted.
    
    This signals that the order passed validation and is queued for fulfillment.
    """
    order_id: str
    customer_id: str
    accepted_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_ship_date: date
    warehouse_id: str
    correlation_id: str

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "order_id": "ord_12345",
                    "customer_id": "cust_67890",
                    "accepted_at": "2026-01-15T10:30:00Z",
                    "estimated_ship_date": "2026-01-17",
                    "warehouse_id": "wh_east_01",
                    "correlation_id": "ord_12345"
                }
            ]
        }


class OrderShipped(BaseModel):
    """
    Event published when an order has been shipped.
    
    Contains tracking information for the customer.
    """
    order_id: str
    customer_id: str
    tracking_number: str
    carrier: Carrier
    shipped_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_delivery_date: date
    warehouse_id: str
    correlation_id: str

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "order_id": "ord_12345",
                    "customer_id": "cust_67890",
                    "tracking_number": "1Z999AA10123456784",
                    "carrier": "UPS",
                    "shipped_at": "2026-01-17T14:00:00Z",
                    "estimated_delivery_date": "2026-01-20",
                    "warehouse_id": "wh_east_01",
                    "correlation_id": "ord_12345"
                }
            ]
        }


class OrderFulfilled(BaseModel):
    """
    Event published when an order has been completely fulfilled.
    
    This is the terminal event in the fulfillment saga.
    """
    order_id: str
    customer_id: str
    fulfilled_at: datetime = Field(default_factory=datetime.utcnow)
    tracking_number: str
    carrier: Carrier
    total_amount: Decimal = Field(decimal_places=2)
    correlation_id: str

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "order_id": "ord_12345",
                    "customer_id": "cust_67890",
                    "fulfilled_at": "2026-01-17T14:00:00Z",
                    "tracking_number": "1Z999AA10123456784",
                    "carrier": "UPS",
                    "total_amount": "79.99",
                    "correlation_id": "ord_12345"
                }
            ]
        }

