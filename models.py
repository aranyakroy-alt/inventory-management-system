from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Supplier(db.Model):
    # Define what information we store about each supplier
    id = db.Column(db.Integer, primary_key=True)  # Unique number for each supplier
    name = db.Column(db.String(100), nullable=False)  # Company name (required)
    contact_person = db.Column(db.String(100))  # Person to contact (optional)
    email = db.Column(db.String(120))  # Email address (optional)
    phone = db.Column(db.String(20))  # Phone number (optional)
    address = db.Column(db.Text)  # Full address (optional)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # When added
    
    # Tell Python: "One supplier can have many products"
    products = db.relationship('Product', backref='supplier', lazy=True)
    
    def __repr__(self):
        return f'<Supplier {self.name}>'

class Product(db.Model):
    # Your existing product information (unchanged)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Connection to supplier (optional so old products don't break)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)
    
    # NEW Phase 4: Relationship to stock transactions
    transactions = db.relationship('StockTransaction', backref='product', lazy=True, order_by='StockTransaction.created_at.desc()')
    
    def __repr__(self):
        return f'<Product {self.name}>'

class StockTransaction(db.Model):
    """
    Phase 4: Track all stock movements for analytics and history
    
    This model logs every change to product quantities, providing:
    - Complete audit trail of stock changes
    - Data for analytics and reporting
    - Foundation for automated alerts and reorder suggestions
    """
    id = db.Column(db.Integer, primary_key=True)
    
    # Link to the product that changed
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    
    # Transaction details
    transaction_type = db.Column(db.String(20), nullable=False)  # 'manual_adjustment', 'sale', 'purchase', 'return', 'correction'
    quantity_change = db.Column(db.Integer, nullable=False)      # positive or negative change
    quantity_before = db.Column(db.Integer, nullable=False)      # stock level before change
    quantity_after = db.Column(db.Integer, nullable=False)       # stock level after change
    
    # Context and reasoning
    reason = db.Column(db.String(200))          # Short reason for the change
    user_notes = db.Column(db.Text)             # Detailed notes if needed
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # When the change occurred
    
    def __repr__(self):
        return f'<StockTransaction {self.product.name}: {self.quantity_change:+d}>'
    
    @property
    def transaction_display(self):
        """Human-friendly transaction description"""
        if self.quantity_change > 0:
            return f"Added {self.quantity_change} units"
        else:
            return f"Removed {abs(self.quantity_change)} units"
    
    @property
    def is_increase(self):
        """True if this transaction increased stock"""
        return self.quantity_change > 0
    
    @property
    def is_decrease(self):
        """True if this transaction decreased stock"""
        return self.quantity_change < 0
    
class ReorderPoint(db.Model):
    """
    Phase 4: Configure automated reorder alerts for products
    
    This model allows setting custom reorder thresholds for each product:
    - When stock falls below minimum_quantity, trigger low stock alerts
    - Suggest reordering reorder_quantity units
    - Can be enabled/disabled per product
    """
    id = db.Column(db.Integer, primary_key=True)
    
    # Link to the product
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, unique=True)
    
    # Reorder configuration
    minimum_quantity = db.Column(db.Integer, default=10, nullable=False)     # Alert when stock drops below this
    reorder_quantity = db.Column(db.Integer, default=50, nullable=False)     # Suggested reorder amount
    is_active = db.Column(db.Boolean, default=True, nullable=False)          # Enable/disable alerts for this product
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship back to product
    product = db.relationship('Product', backref=db.backref('reorder_point', uselist=False))
    
    def __repr__(self):
        return f'<ReorderPoint {self.product.name}: min={self.minimum_quantity}, reorder={self.reorder_quantity}>'
    
    @property
    def is_below_minimum(self):
        """Check if the product is currently below the reorder threshold"""
        return self.is_active and self.product.quantity < self.minimum_quantity
    
    @property
    def alert_level(self):
        """Return alert severity level based on current stock"""
        if not self.is_active:
            return 'disabled'
        
        current = self.product.quantity
        if current == 0:
            return 'critical'  # Out of stock
        elif current < self.minimum_quantity * 0.5:
            return 'urgent'    # Less than half the minimum
        elif current < self.minimum_quantity:
            return 'warning'   # Below minimum but not critical
        else:
            return 'ok'        # Above minimum
    
    @property
    def suggested_order_amount(self):
        """Calculate suggested order quantity to reach reorder level"""
        current = self.product.quantity
        needed_to_reach_reorder = self.reorder_quantity - current
        return max(needed_to_reach_reorder, 0)