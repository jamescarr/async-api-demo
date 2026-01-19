"""
Pydantic models for order events.
"""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

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
    """Event consumed when a new order is created."""
    order_id: str
    customer_id: str
    customer_email: str
    items: list[OrderItem]
    total_amount: Decimal = Field(decimal_places=2)
    shipping_address: Address
    created_at: datetime
    metadata: dict[str, str] = Field(default_factory=dict)


class Carrier(str, Enum):
    """Shipping carrier options."""
    FEDEX = "FEDEX"
    UPS = "UPS"
    USPS = "USPS"
    DHL = "DHL"


class OrderAccepted(BaseModel):
    """Event published when an order is accepted."""
    order_id: str
    customer_id: str
    accepted_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_ship_date: date
    warehouse_id: str


class OrderShipped(BaseModel):
    """Event published when an order is shipped."""
    order_id: str
    customer_id: str
    tracking_number: str
    carrier: Carrier
    shipped_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_delivery_date: date
    warehouse_id: str


class OrderFulfilled(BaseModel):
    """Event published when an order is fulfilled."""
    order_id: str
    customer_id: str
    fulfilled_at: datetime = Field(default_factory=datetime.utcnow)
    tracking_number: str
    carrier: Carrier
    total_amount: Decimal = Field(decimal_places=2)

