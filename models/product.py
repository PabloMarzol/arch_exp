from sqlalchemy import Column, String, Text, DECIMAL, Boolean, DateTime, UUID, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.database import Base
import uuid

class Product(Base):
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    master_name = Column(String(500), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    material = Column(String(100))
    cost_price = Column(DECIMAL(10, 2))
    retail_price = Column(DECIMAL(10, 2))
    wholesale_price = Column(DECIMAL(10, 2))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    mappings = relationship("ProductMapping", back_populates="product")
    inventory = relationship("Inventory", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    production_orders = relationship("ProductionOrder", back_populates="product")

class ProductMapping(Base):
    __tablename__ = "product_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False, index=True)
    platform = Column(String(50), nullable=False)  # 'shopify', 'nuorder', 'quickbooks'
    external_id = Column(String(100))
    external_name = Column(String(500))
    variant_info = Column(Text)  # JSON stored as text
    last_synced = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="mappings")