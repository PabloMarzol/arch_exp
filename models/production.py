from sqlalchemy import Column, String, Integer, DateTime, UUID, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.database import Base
import uuid

class ProductionOrder(Base):
    __tablename__ = "production_orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    quantity_needed = Column(Integer)
    quantity_in_stock = Column(Integer)
    quantity_to_produce = Column(Integer)
    priority = Column(Integer, default=1)
    factory_name = Column(String(200))
    expected_completion = Column(DateTime(timezone=True))
    status = Column(String(50), default='planned')  # 'planned', 'sent_to_factory', 'in_production', 'completed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="production_orders")