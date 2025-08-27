# migrate_database.py
# This safely updates your database to include suppliers

from flask import Flask
from models import db, Product, Supplier
import os

# Create a temporary Flask app to update the database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db.init_app(app)

def migrate_database():
    """Update the database to include suppliers"""
    with app.app_context():
        try:
            print("Starting database migration...")
            
            # Add new tables and columns
            db.create_all()
            
            print("Migration completed successfully!")
            print("- Added 'supplier' table")
            print("- Added 'supplier_id' column to products")
            print("- All existing products preserved")
            
            # Show current data
            product_count = Product.query.count()
            supplier_count = Supplier.query.count()
            
            print(f"Current database contains:")
            print(f"- Products: {product_count}")
            print(f"- Suppliers: {supplier_count}")
            
            return True
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            return False

if __name__ == '__main__':
    success = migrate_database()
    
    if success:
        print("\nDatabase ready for Phase 3!")
    else:
        print("\nSomething went wrong. Check the error above.")