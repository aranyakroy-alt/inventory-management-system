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