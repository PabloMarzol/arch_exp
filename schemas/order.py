from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class OrderBase(BaseModel):
    order_number: str
    platform: str
    customer_info: Optional[str] = None
    order_type: Optional[str] = None
    status: str = "pending"
    total_amount: Optional[Decimal] = None
    order_date: Optional[datetime] = None
    required_date: Optional[datetime] = None
    notes: Optional[str] = None

class OrderCreate(OrderBase):
    pass

class OrderUpdate(OrderBase):
    order_number: Optional[str] = None
    platform: Optional[str] = None
    status: Optional[str] = None

class Order(OrderBase):
    id: UUID4
    created_at: datetime
    
    class Config:
        from_attributes = True