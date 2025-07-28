from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime

class InventoryBase(BaseModel):
    product_id: UUID4
    location: str
    quantity_available: int = 0
    quantity_reserved: int = 0
    quantity_incoming: int = 0
    reorder_point: int = 0

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(InventoryBase):
    product_id: Optional[UUID4] = None
    location: Optional[str] = None
    quantity_available: Optional[int] = None
    quantity_reserved: Optional[int] = None
    quantity_incoming: Optional[int] = None
    reorder_point: Optional[int] = None

class Inventory(InventoryBase):
    id: UUID4
    last_updated: datetime
    
    class Config:
        from_attributes = True