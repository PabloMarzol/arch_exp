# main.py - FastAPI Application
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
from datetime import datetime, timedelta
from services.order_processor import OrderProcessor


from database.database import get_db
from models import Product, Order, Inventory, ProductMapping, ProductionOrder
from models.fashion_extensions import PurchaseOrder, PurchaseOrderItem
import schemas
from services.product_matcher import ProductMatcher

# ------------------------------------------------------------------------------------------------ #
# ------------------------------------------------------------------------------------------------ #


app = FastAPI(title="Business Integration API", version="1.0.0")

# CORS middleware for web dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------------------------ #
# ------ PRODUCTS ------ #
# ------------------------------------------------------------------------------------------------ #

# Product Management Endpoints
@app.post("/products/", response_model=schemas.Product)
async def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    """Create a new master product"""
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/", response_model=List[schemas.Product])
async def list_products(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List products with optional search"""
    query = db.query(Product)
    if search:
        query = query.filter(Product.master_name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()

@app.post("/products/match")
async def match_product(
    name: str, 
    sku: Optional[str] = None,
    platform: str = "unknown",
    external_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Advanced product matching with fuzzy logic"""
    matcher = ProductMatcher(db)
    result = await matcher.find_best_match(
        name=name, 
        sku=sku, 
        platform=platform,
        external_id=external_id
    )
    return result

# ------------------------------------------------------------------------------------------------ #
# ------ INVENTORY ------ #
# ------------------------------------------------------------------------------------------------ #
# Inventory Management
# @app.get("/inventory/summary")
# async def inventory_summary(db: Session = Depends(get_db)):
#     """Get inventory summary across all locations"""
#     manager = InventoryManager(db)
#     return await manager.get_summary()

# @app.post("/inventory/sync")
# async def sync_inventory(platform: str, data: dict, db: Session = Depends(get_db)):
#     """Sync inventory from external platform"""
#     manager = InventoryManager(db)
#     return await manager.sync_from_platform(platform, data)

# # Production Planning
# @app.get("/production/calculate")
# async def calculate_production_needs(db: Session = Depends(get_db)):
#     """Calculate production requirements"""
#     planner = ProductionPlanner(db)
#     return await planner.calculate_needs()

# @app.post("/production/orders")
# async def create_production_order(
#     product_id: str,
#     quantity: int,
#     priority: int = 1,
#     db: Session = Depends(get_db)
# ):
#     """Create new production order"""
#     planner = ProductionPlanner(db)
#     return await planner.create_order(product_id, quantity, priority)


# ------------------------------------------------------------------------------------------------ #
# ------ DASHBOARD ANALYTICS ------ #
# ------------------------------------------------------------------------------------------------ #
@app.get("/analytics/dashboard")
async def dashboard_analytics(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get dashboard analytics data"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Sales analytics
    sales_query = db.query(Order).filter(
        Order.order_date >= start_date,
        Order.order_date <= end_date
    )
    
    # Inventory alerts
    low_stock_query = db.query(Inventory).filter(
        Inventory.quantity_available <= Inventory.reorder_point
    )
    
    return {
        "total_orders": sales_query.count(),
        "total_revenue": sum(o.total_amount for o in sales_query.all()),
        "low_stock_items": low_stock_query.count(),
        "pending_production": db.query(ProductionOrder).filter(
            ProductionOrder.status.in_(['planned', 'sent_to_factory'])
        ).count()
    }
    
@app.get("/sync/status")
async def get_sync_status():
    """Get integration sync status"""
    # This will be implemented properly later based on client's specific platforms
    return {
        "shopify": {
            "status": "connected",
            "last_sync": "2025-01-26T10:30:00Z"
        },
        "nuorder": {
            "status": "syncing", 
            "last_sync": "2025-01-26T10:25:00Z"
        },
        "quickbooks": {
            "status": "connected",
            "last_sync": "2025-01-26T10:35:00Z"
        }
    }
    
    
# ------------------------------------------------------------------------------------------------ #
# ------ ORDERS ------ #
# ------------------------------------------------------------------------------------------------ #
@app.post("/orders/process-csv")
async def process_order_csv(
    file_path: str,
    db: Session = Depends(get_db)
):
    """Process NuOrder CSV file"""
    processor = OrderProcessor(db)
    result = await processor.process_nuorder_csv(file_path)
    return result

@app.get("/orders/sync-inventory/{po_id}")
async def sync_po_inventory(
    po_id: str,
    db: Session = Depends(get_db)
):
    """Sync PO with inventory - client's biggest pain point"""
    processor = OrderProcessor(db)
    result = await processor.sync_po_with_inventory(po_id)
    return result

@app.get("/orders/purchase-orders")
async def list_purchase_orders(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all purchase orders"""
    query = db.query(PurchaseOrder)
    if status:
        query = query.filter(PurchaseOrder.status == status)
    
    orders = query.order_by(PurchaseOrder.order_date.desc()).all()
    
    return [{
        "id": str(order.id),
        "po_number": order.po_number,
        "customer_name": order.customer_name,
        "total_skus": order.total_skus,
        "total_units": order.total_units,
        "status": order.status,
        "order_date": order.order_date.isoformat() if order.order_date else None
    } for order in orders]