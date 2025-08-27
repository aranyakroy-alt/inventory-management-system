# verify_migration.py
# Quick test to confirm everything works before continuing

from flask import Flask
from models import db, Product, Supplier

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db.init_app(app)

def verify_setup():
    """Test that supplier functionality is ready"""
    with app.app_context():
        try:
            # Test 1: Can we count existing products?
            product_count = Product.query.count()
            print(f"Test 1 - Found {product_count} existing products")
            
            # Test 2: Can we count suppliers?
            supplier_count = Supplier.query.count()
            print(f"Test 2 - Found {supplier_count} suppliers")
            
            # Test 3: Can we access supplier_id on products?
            if product_count > 0:
                sample_product = Product.query.first()
                supplier_id = sample_product.supplier_id
                print(f"Test 3 - Product supplier_id field: {supplier_id} (should be None)")
            
            print("All tests passed - ready for Phase 3!")
            return True
            
        except Exception as e:
            print(f"Verification failed: {str(e)}")
            return False

if __name__ == '__main__':
    success = verify_setup()
    if success:
        print("Database migration successful. Ready to build supplier features.")
    else:
        print("Issues found. Need to fix before continuing.")