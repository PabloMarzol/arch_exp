from sqlalchemy import Column, String, DECIMAL, DateTime, Date, UUID, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.database import Base
import uuid

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'), nullable=False)
    quickbooks_invoice_id = Column(String(100))
    invoice_number = Column(String(100))
    amount = Column(DECIMAL(10, 2))
    status = Column(String(50), default='draft')  # 'draft', 'sent', 'paid', 'overdue'
    due_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="invoices")