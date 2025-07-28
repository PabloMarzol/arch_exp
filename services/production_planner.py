# services/production_planner.py
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from models import Product, Order, OrderItem, Inventory, ProductionOrder

class ProductionPlanner:
    def __init__(self, db: Session):
        self.db = db
        self.safety_stock_percentage = 0.1  # 10% safety stock
    
    async def calculate_needs(self) -> List[Dict]:
        """
        Calculate production needs based on:
        1. Pending orders
        2. Current inventory levels
        3. Incoming production
        4. Safety stock requirements
        """
        
        # Get all pending orders and their requirements
        pending_orders = self.db.query(
            Product.id,
            Product.master_name,
            Product.sku,
            func.sum(OrderItem.quantity).label('total_needed')
        ).join(
            OrderItem, Product.id == OrderItem.product_id
        ).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            Order.status.in_(['pending', 'processing', 'confirmed'])
        ).group_by(
            Product.id, Product.master_name, Product.sku
        ).all()
        
        production_needs = []
        
        for order_data in pending_orders:
            # Get current inventory across all locations
            inventory_total = self.db.query(
                func.sum(Inventory.quantity_available)
            ).filter(
                Inventory.product_id == order_data.id
            ).scalar() or 0
            
            # Get incoming production
            incoming_production = self.db.query(
                func.sum(ProductionOrder.quantity_to_produce)
            ).filter(
                ProductionOrder.product_id == order_data.id,
                ProductionOrder.status.in_(['planned', 'sent_to_factory', 'in_production'])
            ).scalar() or 0
            
            # Calculate safety stock (10% of monthly average sales)
            monthly_avg = self._calculate_monthly_average(order_data.id)
            safety_stock = int(monthly_avg * self.safety_stock_percentage)
            
            # Total requirement = Orders + Safety Stock
            total_requirement = order_data.total_needed + safety_stock
            
            # Available = Current Stock + Incoming Production
            total_available = inventory_total + incoming_production
            
            # Calculate what we need to produce
            need_to_produce = max(0, total_requirement - total_available)
            
            if need_to_produce > 0:
                production_needs.append({
                    'product_id': order_data.id,
                    'product_name': order_data.master_name,
                    'sku': order_data.sku,
                    'orders_pending': order_data.total_needed,
                    'current_stock': inventory_total,
                    'incoming_production': incoming_production,
                    'safety_stock_needed': safety_stock,
                    'total_needed': total_requirement,
                    'total_available': total_available,
                    'to_produce': need_to_produce,
                    'priority': self._calculate_priority(order_data.id)
                })
        
        # Sort by priority (high priority first)
        production_needs.sort(key=lambda x: x['priority'], reverse=True)
        
        return production_needs
    
    def _calculate_monthly_average(self, product_id: str) -> float:
        """Calculate monthly average sales for safety stock calculation"""
        three_months_ago = datetime.now() - timedelta(days=90)
        
        total_sold = self.db.query(
            func.sum(OrderItem.quantity)
        ).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            OrderItem.product_id == product_id,
            Order.order_date >= three_months_ago,
            Order.status == 'completed'
        ).scalar() or 0
        
        return total_sold / 3  # Monthly average
    
    def _calculate_priority(self, product_id: str) -> int:
        """
        Calculate production priority based on:
        1. Urgency of pending orders
        2. Historical sales velocity
        3. Customer importance
        """
        # Get earliest required date for pending orders
        earliest_date = self.db.query(
            func.min(Order.required_date)
        ).join(
            OrderItem, Order.id == OrderItem.order_id
        ).filter(
            OrderItem.product_id == product_id,
            Order.status.in_(['pending', 'processing'])
        ).scalar()
        
        if earliest_date:
            days_until_needed = (earliest_date - datetime.now().date()).days
            if days_until_needed <= 7:
                return 5  # Critical
            elif days_until_needed <= 14:
                return 4  # High
            elif days_until_needed <= 30:
                return 3  # Medium
            else:
                return 2  # Normal
        
        return 1  # Low priority
    
    async def create_order(self, product_id: str, quantity: int, priority: int = 1) -> ProductionOrder:
        """Create a new production order"""
        production_order = ProductionOrder(
            product_id=product_id,
            quantity_to_produce=quantity,
            priority=priority,
            status='planned',
            created_at=datetime.now()
        )
        
        self.db.add(production_order)
        self.db.commit()
        self.db.refresh(production_order)
        
        return production_order