import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import io
import base64


# ------------------------------------------------------------------------------------------------ #
# =================== PAGE CONFIG ======================== #
# ------------------------------------------------------------------------------------------------ #
st.set_page_config(
    page_title="ARCH4 Business Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .status-connected { color: #4CAF50; }
    .status-syncing { color: #FF9800; }
    .status-error { color: #F44336; }
</style>
""", unsafe_allow_html=True)

# API base URL
API_BASE = "http://localhost:8000"

@st.cache_data(ttl=30)  # Cache for 30 seconds
def fetch_dashboard_data():
    """Fetch dashboard data from FastAPI backend"""
    try:
        response = requests.get(f"{API_BASE}/analytics/dashboard", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to backend API: {e}")
        return {"total_orders": 0, "total_revenue": 0, "low_stock_items": 0, "pending_production": 0}

@st.cache_data(ttl=30)
def fetch_sync_status():
    """Fetch integration sync status"""
    try:
        response = requests.get(f"{API_BASE}/sync/status", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Could not fetch sync status: {e}")
        return {}

@st.cache_data(ttl=60)
def fetch_products():
    """Fetch products from API"""
    try:
        response = requests.get(f"{API_BASE}/products/", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Could not fetch products: {e}")
        return []


# ------------------------------------------------------------------------------------------------ #
# =================== MAIN FUNCTIONS ======================== #
# ------------------------------------------------------------------------------------------------ #
# ------------------------------------------------------------------------------------------------ #
def show_dashboard():
    """Main dashboard page"""
    st.markdown('<div class="main-header"><h1>🏢 ARCH4 Business Integration Dashboard</h1></div>', unsafe_allow_html=True)
    
    # Fetch data
    dashboard_data = fetch_dashboard_data()
    sync_status = fetch_sync_status()
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Total Orders",
            value=dashboard_data.get('total_orders', 0),
            delta=None
        )
    
    with col2:
        revenue = dashboard_data.get('total_revenue', 0)
        st.metric(
            label="💰 Revenue (30d)",
            value=f"£{revenue:,.2f}",
            delta=None
        )
    
    with col3:
        low_stock = dashboard_data.get('low_stock_items', 0)
        st.metric(
            label="⚠️ Low Stock Items",
            value=low_stock,
            delta=None
        )
    
    with col4:
        pending_prod = dashboard_data.get('pending_production', 0)
        st.metric(
            label="🏭 Pending Production",
            value=pending_prod,
            delta=None
        )
    
    st.divider()
    
    # Integration status
    st.subheader("🔄 Integration Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        shopify_status = sync_status.get('shopify', {})
        status = shopify_status.get('status', 'unknown')
        status_color = 'status-connected' if status == 'connected' else 'status-error'
        
        st.markdown(f"""
        **🛒 Shopify**  
        <span class="{status_color}">● {status.title()}</span>
        """, unsafe_allow_html=True)
        
        if shopify_status.get('last_sync'):
            last_sync = datetime.fromisoformat(shopify_status['last_sync'].replace('Z', '+00:00'))
            st.caption(f"Last sync: {last_sync.strftime('%Y-%m-%d %H:%M')}")
    
    with col2:
        nuorder_status = sync_status.get('nuorder', {})
        status = nuorder_status.get('status', 'unknown')
        status_color = 'status-syncing' if status == 'syncing' else 'status-connected' if status == 'connected' else 'status-error'
        
        st.markdown(f"""
        **📋 NuOrder**  
        <span class="{status_color}">● {status.title()}</span>
        """, unsafe_allow_html=True)
        
        if nuorder_status.get('last_sync'):
            last_sync = datetime.fromisoformat(nuorder_status['last_sync'].replace('Z', '+00:00'))
            st.caption(f"Last sync: {last_sync.strftime('%Y-%m-%d %H:%M')}")
    
    with col3:
        qb_status = sync_status.get('quickbooks', {})
        status = qb_status.get('status', 'unknown')
        status_color = 'status-connected' if status == 'connected' else 'status-error'
        
        st.markdown(f"""
        **🧾 QuickBooks**  
        <span class="{status_color}">● {status.title()}</span>
        """, unsafe_allow_html=True)
        
        if qb_status.get('last_sync'):
            last_sync = datetime.fromisoformat(qb_status['last_sync'].replace('Z', '+00:00'))
            st.caption(f"Last sync: {last_sync.strftime('%Y-%m-%d %H:%M')}")

def show_products():
    """Products management page"""
    st.title("📦 Product Management")
    
    # Add new product form
    with st.expander("➕ Add New Product"):
        with st.form("add_product"):
            col1, col2 = st.columns(2)
            
            with col1:
                sku = st.text_input("SKU*", placeholder="e.g., KNIGHT001")
                master_name = st.text_input("Product Name*", placeholder="e.g., Knightsbridge Luxury Watch")
                category = st.text_input("Category", placeholder="e.g., Watches")
                material = st.text_input("Material", placeholder="e.g., Gold")
            
            with col2:
                cost_price = st.number_input("Cost Price (£)", min_value=0.0, format="%.2f")
                retail_price = st.number_input("Retail Price (£)", min_value=0.0, format="%.2f")
                wholesale_price = st.number_input("Wholesale Price (£)", min_value=0.0, format="%.2f")
                active = st.checkbox("Active", value=True)
            
            description = st.text_area("Description", placeholder="Product description...")
            
            submitted = st.form_submit_button("Create Product")
            
            if submitted and sku and master_name:
                # Create product via API
                product_data = {
                    "sku": sku,
                    "master_name": master_name,
                    "description": description,
                    "category": category,
                    "material": material,
                    "cost_price": cost_price,
                    "retail_price": retail_price,
                    "wholesale_price": wholesale_price,
                    "active": active
                }
                
                try:
                    response = requests.post(f"{API_BASE}/products/", json=product_data)
                    if response.status_code == 200:
                        st.success("✅ Product created successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Error creating product: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Could not create product: {e}")
    
    # Search and filters
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("🔍 Search products", placeholder="Search by name or SKU...")
    with col2:
        show_inactive = st.checkbox("Show inactive products")
    with col3:
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()
    
    # Products list
    products = fetch_products()
    
    if products:
        # Convert to DataFrame for easier display
        df = pd.DataFrame(products)
        
        # Apply filters
        if search_term:
            mask = df['master_name'].str.contains(search_term, case=False, na=False) | \
                   df['sku'].str.contains(search_term, case=False, na=False)
            df = df[mask]
        
        if not show_inactive:
            df = df[df['active'] == True]
        
        # Display products
        st.subheader(f"Products ({len(df)} found)")
        
        if not df.empty:
            # Format the DataFrame for display
            display_df = df[['sku', 'master_name', 'category', 'retail_price', 'wholesale_price', 'active']].copy()
            display_df['retail_price'] = display_df['retail_price'].apply(lambda x: f"£{x:.2f}" if pd.notna(x) else "")
            display_df['wholesale_price'] = display_df['wholesale_price'].apply(lambda x: f"£{x:.2f}" if pd.notna(x) else "")
            display_df.columns = ['SKU', 'Product Name', 'Category', 'Retail Price', 'Wholesale Price', 'Active']
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No products found matching your criteria.")
    else:
        st.info("No products available. Create your first product above!")

def show_product_matching():
    """Product matching test page"""
    st.title("🔍 Product Matching Test")
    
    st.info("Test the fuzzy product matching algorithm used for platform integration.")
    
    with st.form("product_match_test"):
        col1, col2 = st.columns(2)
        
        with col1:
            product_name = st.text_input("Product Name", placeholder="e.g., nice bridge watch")
            sku = st.text_input("SKU (optional)", placeholder="e.g., KNIGHT001")
        
        with col2:
            platform = st.selectbox("Platform", ["shopify", "nuorder", "quickbooks"])
            external_id = st.text_input("External ID", placeholder="e.g., shop_123")
        
        submitted = st.form_submit_button("🔍 Test Match")
        
        if submitted and product_name:
            try:
                params = {
                    "name": product_name,
                    "platform": platform,
                    "external_id": external_id
                }
                if sku:
                    params["sku"] = sku
                
                response = requests.post(f"{API_BASE}/products/match", params=params)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.subheader("Match Result:")
                    
                    confidence = result.get('confidence', 0)
                    match_type = result.get('match_type', 'unknown')
                    
                    # Show confidence with color coding
                    if confidence >= 0.8:
                        st.success(f"✅ High Confidence Match: {confidence:.1%}")
                    elif confidence >= 0.5:
                        st.warning(f"⚠️ Medium Confidence Match: {confidence:.1%}")
                    else:
                        st.error(f"❌ Low Confidence Match: {confidence:.1%}")
                    
                    # Show details
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Match Type:**", match_type)
                        if result.get('product_id'):
                            st.write("**Product ID:**", result['product_id'])
                    
                    with col2:
                        if result.get('matched_name'):
                            st.write("**Matched Product:**", result['matched_name'])
                        if result.get('message'):
                            st.info(result['message'])
                
                else:
                    st.error(f"Error testing match: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Could not test match: {e}")


def show_order_processing():
    """Order processing page - Client's #1 priority"""
    st.title("📋 Order Processing")
    st.info("Process NuOrder CSV files and sync with inventory - solving your biggest pain point!")
    
    # Upload CSV file
    st.subheader("📤 Upload NuOrder CSV")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose CSV file from NuOrder",
            type=['csv'],
            help="Upload your NuOrder export with: PO number, customer name, style, price, color, size, collection name"
        )
    
    with col2:
        st.markdown("**Expected CSV format:**")
        st.code("""
po_number,customer_name,style,price,color,size,collection_name,quantity
PO-001,Customer ABC,Knightsbridge Jacket,150.00,Black,M,Spring 2025,10
PO-001,Customer ABC,Knightsbridge Jacket,150.00,Navy,L,Spring 2025,15
        """)
    
    if uploaded_file is not None:
        try:
            # Preview the CSV
            import pandas as pd
            df = pd.read_csv(uploaded_file)
            
            st.subheader("📊 CSV Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Show summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", len(df))
            with col2:
                unique_pos = df['po_number'].nunique() if 'po_number' in df.columns else 0
                st.metric("Unique POs", unique_pos)
            with col3:
                total_qty = df['quantity'].sum() if 'quantity' in df.columns else 0
                st.metric("Total Units", total_qty)
            
            # Process button
            if st.button("🚀 Process Orders", type="primary"):
                with st.spinner("Processing orders..."):
                    # Save uploaded file temporarily
                    import tempfile
                    import os
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                        df.to_csv(f.name, index=False)
                        temp_file_path = f.name
                    
                    try:
                        # Call API to process
                        response = requests.post(
                            f"{API_BASE}/orders/process-csv",
                            params={"file_path": temp_file_path}
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result['success']:
                                st.success(f"✅ {result['message']}")
                                
                                # Show processed orders
                                st.subheader("📦 Processed Orders")
                                processed_df = pd.DataFrame(result['orders'])
                                st.dataframe(processed_df, use_container_width=True)
                                
                                # Clear cache to show updated data
                                st.cache_data.clear()
                                
                            else:
                                st.error(f"❌ Processing failed: {result['error']}")
                        else:
                            st.error(f"❌ API Error: {response.text}")
                    
                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)
        
        except Exception as e:
            st.error(f"❌ Error reading CSV: {e}")
    
    st.divider()
    
    # Show existing purchase orders
    st.subheader("📋 Recent Purchase Orders")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "received", "processed", "invoiced", "shipped"])
    with col2:
        if st.button("🔄 Refresh Orders"):
            st.cache_data.clear()
    
    # Fetch orders
    try:
        params = {} if status_filter == "All" else {"status": status_filter}
        response = requests.get(f"{API_BASE}/orders/purchase-orders", params=params)
        
        if response.status_code == 200:
            orders = response.json()
            
            if orders:
                # Convert to DataFrame for better display
                df = pd.DataFrame(orders)
                
                # Format the DataFrame
                if 'order_date' in df.columns:
                    df['order_date'] = pd.to_datetime(df['order_date']).dt.strftime('%Y-%m-%d %H:%M')
                
                # Display with action buttons
                for i, order in enumerate(orders):
                    with st.expander(f"📦 {order['po_number']} - {order['customer_name']} ({order['status']})"):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.write(f"**PO Number:** {order['po_number']}")
                            st.write(f"**Customer:** {order['customer_name']}")
                        
                        with col2:
                            st.write(f"**SKUs:** {order['total_skus']}")
                            st.write(f"**Units:** {order['total_units']}")
                        
                        with col3:
                            st.write(f"**Status:** {order['status']}")
                            if order.get('order_date'):
                                st.write(f"**Date:** {order['order_date']}")
                        
                        with col4:
                            # The magic button - solves their biggest pain point!
                            if st.button(f"🔍 Sync with Inventory", key=f"sync_{order['id']}"):
                                sync_po_with_inventory(order['id'], order['po_number'])
            else:
                st.info("No purchase orders found. Upload a CSV file to get started!")
        
        else:
            st.error("Could not fetch purchase orders")
    
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to API: {e}")

def sync_po_with_inventory(po_id: str, po_number: str):
    """Sync PO with inventory - the client's biggest pain point solution!"""
    with st.spinner(f"Syncing {po_number} with inventory..."):
        try:
            response = requests.get(f"{API_BASE}/orders/sync-inventory/{po_id}")
            
            if response.status_code == 200:
                result = response.json()
                
                if result['success']:
                    st.success(f"✅ Inventory sync complete for {result['po_number']}")
                    
                    # Show detailed availability report
                    st.subheader(f"📊 Inventory Report - {result['po_number']}")
                    
                    # Summary metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Items", result['total_items'])
                    with col2:
                        st.metric("✅ In Stock", result['items_in_stock'])
                    with col3:
                        st.metric("⚠️ Short", result['items_short'])
                    
                    # Detailed breakdown
                    availability_df = pd.DataFrame(result['availability'])
                    
                    # Color code the status
                    def color_status(val):
                        if val == 'in_stock':
                            return 'background-color: #d4edda'
                        else:
                            return 'background-color: #f8d7da'
                    
                    styled_df = availability_df.style.applymap(
                        color_status, subset=['status']
                    )
                    
                    st.dataframe(styled_df, use_container_width=True)
                    
                    # Show production requirements for short items
                    short_items = availability_df[availability_df['status'] == 'short']
                    if len(short_items) > 0:
                        st.warning(f"⚠️ {len(short_items)} items need production")
                        
                        with st.expander("📋 Production Requirements"):
                            st.dataframe(
                                short_items[['style', 'color', 'size', 'shortfall']],
                                use_container_width=True
                            )
                            
                            if st.button("📧 Email Factory Requirements"):
                                send_factory_email(short_items)
                    
                    else:
                        st.success("🎉 All items are in stock! Ready to fulfill.")
                
                else:
                    st.error(f"❌ Sync failed: {result['error']}")
            
            else:
                st.error(f"❌ API Error: {response.text}")
        
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Could not sync inventory: {e}")

def send_factory_email(short_items_df):
    """Generate factory email - matches client's current email process"""
    st.subheader("📧 Factory Email Preview")
    
    # Generate email content based on client's format: "style name, size and quantity"
    email_content = "Dear Factory Team,\n\nPlease arrange production for the following items:\n\n"
    
    for _, item in short_items_df.iterrows():
        email_content += f"• {item['style']}, {item['color']}, {item['size']}: {item['shortfall']} units\n"
    
    email_content += f"\nTotal items: {len(short_items_df)}\n"
    email_content += f"Total units needed: {short_items_df['shortfall'].sum()}\n"
    email_content += "\nPlease confirm receipt and expected completion date.\n\nBest regards,\nARCH4 Team"
    
    st.text_area("Email Content", email_content, height=200)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Copy to Clipboard"):
            st.success("✅ Email content copied! (In real implementation)")
    
    with col2:
        if st.button("📧 Send Email"):
            st.success("✅ Email sent to factory! (In real implementation)")

def show_inventory_overview():
    """Inventory overview page"""
    st.title("📦 Inventory Overview")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total SKUs", "2,354", help="From Shopify")
    with col2:
        st.metric("Locations", "4", help="NYC, Hong Kong, China, London")
    with col3:
        st.metric("Low Stock Items", "47", delta="-5")
    with col4:
        st.metric("Out of Stock", "12", delta="2")
    
    # Location breakdown
    st.subheader("📍 Stock by Location")
    
    # Mock data for now - will be real data later
    location_data = {
        'Location': ['London (Main)', 'NYC', 'Hong Kong', 'China (Factory)'],
        'Total SKUs': [2354, 1200, 800, 500],
        'In Stock': [2100, 1100, 750, 480],
        'Low Stock': [200, 80, 40, 15],
        'Out of Stock': [54, 20, 10, 5]
    }
    
    df = pd.DataFrame(location_data)
    st.dataframe(df, use_container_width=True)
    
    # Search functionality
    st.subheader("🔍 Product Search")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input("Search by style name", placeholder="e.g., Knightsbridge")
    with col2:
        color_filter = st.selectbox("Color", ["All", "Black", "Navy", "Brown", "Grey"])
    with col3:
        size_filter = st.selectbox("Size", ["All", "XS", "S", "M", "L", "XL"])
    
    if search_term:
        st.info(f"🔍 Searching for '{search_term}'... (Will connect to real inventory data)")



# ------------------------------------------------------------------------------------------------ #
# =================== MAIN APP ======================== #
# ------------------------------------------------------------------------------------------------ #

def main():
    # Sidebar navigation
    st.sidebar.title("🏢 ARCH4 Navigation")
    
    pages = {
        "📊 Dashboard": show_dashboard,
        "📋 Order Processing": show_order_processing,  # New - Priority #1
        "📦 Inventory Overview": show_inventory_overview,  # New
        "📦 Products": show_products,
        "🔍 Product Matching": show_product_matching,
    }
    
    selected_page = st.sidebar.selectbox("Choose a page", list(pages.keys()))
    
    # Add refresh button in sidebar
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Add connection status in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔌 API Connection")
    
    try:
        response = requests.get(f"{API_BASE}/analytics/dashboard", timeout=2)
        if response.status_code == 200:
            st.sidebar.success("✅ Connected")
        else:
            st.sidebar.error("❌ API Error")
    except requests.exceptions.RequestException:
        st.sidebar.error("❌ Disconnected")
        st.sidebar.caption("Make sure FastAPI is running on port 8000")
    
    # Show selected page
    pages[selected_page]()

if __name__ == "__main__":
    main()