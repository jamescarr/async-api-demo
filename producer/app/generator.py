"""
Random order generator using Faker.

This module creates realistic-looking order data for demonstration purposes.
"""
import random
import uuid
from decimal import Decimal
from faker import Faker

from .models import OrderCreated, OrderItem, Address

fake = Faker()

# Sample product catalog
PRODUCTS = [
    ("prod_001", "Wireless Headphones", Decimal("79.99")),
    ("prod_002", "Mechanical Keyboard", Decimal("149.99")),
    ("prod_003", "USB-C Hub", Decimal("49.99")),
    ("prod_004", "4K Monitor", Decimal("399.99")),
    ("prod_005", "Ergonomic Mouse", Decimal("69.99")),
    ("prod_006", "Webcam HD", Decimal("89.99")),
    ("prod_007", "Laptop Stand", Decimal("45.99")),
    ("prod_008", "Cable Management Kit", Decimal("24.99")),
    ("prod_009", "Desk Mat", Decimal("34.99")),
    ("prod_010", "Blue Light Glasses", Decimal("29.99")),
]


def generate_order_item() -> OrderItem:
    """Generate a random order item from our catalog."""
    product_id, product_name, unit_price = random.choice(PRODUCTS)
    return OrderItem(
        product_id=product_id,
        product_name=product_name,
        quantity=random.randint(1, 3),
        unit_price=unit_price,
    )


def generate_address() -> Address:
    """Generate a random US address."""
    return Address(
        street=fake.street_address(),
        city=fake.city(),
        state=fake.state_abbr(),
        zip_code=fake.zipcode(),
        country="USA",
    )


def generate_order() -> OrderCreated:
    """Generate a complete random order."""
    # Generate 1-4 items per order
    items = [generate_order_item() for _ in range(random.randint(1, 4))]
    
    # Calculate total
    total = sum(item.unit_price * item.quantity for item in items)
    
    # Random metadata
    sources = ["web", "mobile", "api", "pos"]
    campaigns = ["holiday_sale", "summer_promo", "new_customer", "loyalty_reward", None]
    
    metadata = {"source": random.choice(sources)}
    campaign = random.choice(campaigns)
    if campaign:
        metadata["campaign"] = campaign
    
    return OrderCreated(
        order_id=f"ord_{uuid.uuid4().hex[:12]}",
        customer_id=f"cust_{uuid.uuid4().hex[:8]}",
        customer_email=fake.email(),
        items=items,
        total_amount=total,
        shipping_address=generate_address(),
        metadata=metadata,
    )

