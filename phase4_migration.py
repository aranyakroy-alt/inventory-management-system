# phase4_migration.py
# Phase 4: Add transaction logging to existing database

from flask import Flask
from models import db, Product, Supplier, StockTransaction
import os

# Create Flask app for migration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db.init_app(app)

def migrate_to_phase4():
    """Add transaction logging table to existing database"""
    print("Starting Phase 4 Database Migration...")
    print("Adding transaction logging capabilities to your inventory system")
    print("-" * 60)
    
    with app.app_context():
        try:
            # Step 1: Verify current state
            print("Step 1: Checking current database state...")
            product_count = Product.query.count()
            supplier_count = Supplier.query.count()
            
            print(f"✅ Current database contains:")
            print(f"   - Products: {product_count}")
            print(f"   - Suppliers: {supplier_count}")
            
            # Step 2: Create new tables (StockTransaction)
            print("\nStep 2: Creating new transaction logging table...")
            db.create_all()  # This will create any missing tables, including StockTransaction
            print("✅ StockTransaction table created successfully")
            
            # Step 3: Verify new table was created
            print("\nStep 3: Verifying transaction table...")
            # Try to query the new table (will fail if table doesn't exist)
            transaction_count = StockTransaction.query.count()
            print(f"✅ StockTransaction table ready (contains {transaction_count} transactions)")
            
            # Step 4: Show migration results
            print("\nPhase 4 Migration Results:")
            print("=" * 40)
            print("✅ Transaction logging system ready")
            print("✅ All existing data preserved:")
            print(f"   - {product_count} products maintained")
            print(f"   - {supplier_count} suppliers maintained")
            print("✅ New features available:")
            print("   - Stock movement tracking")
            print("   - Transaction history")
            print("   - Foundation for analytics dashboard")
            
            print(f"\nNext steps:")
            print("1. Update your models.py with the new StockTransaction model")
            print("2. Modify stock adjustment routes to log transactions")
            print("3. Create transaction history views")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            print("Your existing data is safe and unchanged.")
            return False

if __name__ == '__main__':
    success = migrate_to_phase4()
    
    if success:
        print("\n🎉 Phase 4 Migration Complete!")
        print("Your database is ready for smart inventory features.")
        print("You can now start logging stock transactions!")
    else:
        print("\n⚠️  Migration encountered issues.")
        print("Please check the errors above and try again.")