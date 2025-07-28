from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.database import Base
import uuid
from sqlalchemy import UUID

class Collection(Base):
    __tablename__ = "collections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)  # e.g., "Spring 2025"
    season = Column(String(50))  # spring, summer, fall, winter
    year = Column(Integer)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # NO products relationship - this was causing the error

class Style(Base):
    __tablename__ = "styles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    style_name = Column(String(200), nullable=False)  # e.g., "Knightsbridge Jacket"
    style_code = Column(String(50), unique=True)  # internal style code
    collection_id = Column(UUID(as_uuid=True), ForeignKey('collections.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    collection = relationship("Collection")
    variants = relationship("ProductVariant", back_populates="style")

class ProductVariant(Base):
    __tablename__ = "product_variants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'))
    style_id = Column(UUID(as_uuid=True), ForeignKey('styles.id'))
    
    # Fashion-specific attributes
    color = Column(String(50))
    size = Column(String(20))
    material = Column(String(100))
    season = Column(String(50))
    
    # Pricing
    cost_price = Column(Float)
    wholesale_price = Column(Float)
    retail_price = Column(Float)
    
    # Inventory
    sku = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product")
    style = relationship("Style", back_populates="variants")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number = Column(String(100), unique=True, nullable=False)
    customer_name = Column(String(200))
    platform = Column(String(50))  # 'nuorder', 'shopify'
    
    # Order details matching client's requirements
    collection_name = Column(String(200))
    total_skus = Column(Integer)  # around 30 SKUs per order
    total_units = Column(Integer)  # 100-1000 units
    
    # Status tracking
    status = Column(String(50), default='received')  # received, processed, invoiced, shipped
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    required_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    line_items = relationship("PurchaseOrderItem", back_populates="purchase_order")

class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_id = Column(UUID(as_uuid=True), ForeignKey('purchase_orders.id'))
    
    # Product details (matching client's PO format)
    style_name = Column(String(200))
    color = Column(String(50))
    size = Column(String(20))
    quantity = Column(Integer)
    unit_price = Column(Float)
    total_price = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="line_items")