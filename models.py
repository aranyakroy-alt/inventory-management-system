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
    
    # NEW: Connection to supplier (optional so old products don't break)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)
    
    def __repr__(self):
        return f'<Product {self.name}>'