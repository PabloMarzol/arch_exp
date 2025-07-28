from sqlalchemy import Column, String, Integer, DECIMAL, DateTime, UUID, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.database import Base
import uuid

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(100), unique=True, nullable=False, index=True)
    platform = Column(String(50), nullable=False)  # 'shopify', 'nuorder'
    customer_info = Column(Text)  # JSON stored as text
    order_type = Column(String(50))  # 'retail', 'wholesale'
    status = Column(String(50), default='pending')  # 'pending', 'processing', 'shipped', 'delivered'
    total_amount = Column(DECIMAL(10, 2))
    order_date = Column(DateTime(timezone=True))
    required_date = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="order")
    invoices = relationship("Invoice", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2))
    total_price = Column(DECIMAL(10, 2))
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")