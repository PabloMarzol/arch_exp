from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime
from decimal import Decimal

class ProductBase(BaseModel):
    sku: str
    master_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    material: Optional[str] = None
    cost_price: Optional[Decimal] = None
    retail_price: Optional[Decimal] = None
    wholesale_price: Optional[Decimal] = None
    active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    sku: Optional[str] = None
    master_name: Optional[str] = None
    active: Optional[bool] = None

class Product(ProductBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True