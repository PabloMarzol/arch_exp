import pandas as pd
from sqlalchemy.orm import Session
from models import PurchaseOrder, PurchaseOrderItem, ProductVariant
from typing import Dict, List
import uuid
from datetime import datetime

class OrderProcessor:
    """
    Handles order processing from NuOrder/CSV imports
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def process_nuorder_csv(self, csv_file_path: str) -> Dict:
        """
        Process NuOrder CSV export
        Format: PO number, customer name, style, price, color, size, collection name
        """
        try:
            # Read CSV with polars
            import polars as pl
            df = pl.read_csv(csv_file_path)
            
            # Group by PO number to create purchase orders
            po_groups = df.group_by("po_number")
            
            processed_orders = []
            
            for po_number, po_data in po_groups:
                # Create purchase order
                po = PurchaseOrder(
                    po_number=po_number,
                    customer_name=po_data["customer_name"][0],
                    platform="nuorder",
                    collection_name=po_data["collection_name"][0],
                    total_skus=len(po_data),
                    total_units=po_data["quantity"].sum(),
                    status="received",
                    order_date=datetime.now()
                )
                
                self.db.add(po)
                self.db.flush()  # Get the ID
                
                # Create line items
                for row in po_data.iter_rows(named=True):
                    line_item = PurchaseOrderItem(
                        po_id=po.id,
                        style_name=row["style"],
                        color=row["color"],
                        size=row["size"],
                        quantity=row["quantity"],
                        unit_price=row["price"],
                        total_price=row["quantity"] * row["price"]
                    )
                    self.db.add(line_item)
                
                processed_orders.append({
                    "po_number": po_number,
                    "customer": po.customer_name,
                    "total_skus": po.total_skus,
                    "total_units": po.total_units
                })
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Processed {len(processed_orders)} purchase orders",
                "orders": processed_orders
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def sync_po_with_inventory(self, po_id: str) -> Dict:
        """
        Client's biggest pain point: "sync PO with inventory"
        This automates their most time-consuming task
        """
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        if not po:
            return {"success": False, "error": "Purchase order not found"}
        
        availability_report = []
        
        for item in po.line_items:
            # Find matching product variants
            variants = self.db.query(ProductVariant).filter(
                ProductVariant.style_name.ilike(f"%{item.style_name}%"),
                ProductVariant.color == item.color,
                ProductVariant.size == item.size
            ).all()
            
            total_available = sum([
                inv.quantity_available for variant in variants 
                for inv in variant.product.inventory
            ])
            
            availability_report.append({
                "style": item.style_name,
                "color": item.color,
                "size": item.size,
                "requested": item.quantity,
                "available": total_available,
                "shortfall": max(0, item.quantity - total_available),
                "status": "in_stock" if total_available >= item.quantity else "short"
            })
        
        return {
            "success": True,
            "po_number": po.po_number,
            "customer": po.customer_name,
            "availability": availability_report,
            "total_items": len(availability_report),
            "items_in_stock": len([item for item in availability_report if item["status"] == "in_stock"]),
            "items_short": len([item for item in availability_report if item["status"] == "short"])
        }