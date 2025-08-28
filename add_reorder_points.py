# add_reorder_points.py
# Phase 4: Add reorder point management to existing database

from flask import Flask
from models import db, Product, Supplier, StockTransaction, ReorderPoint
import os

# Create Flask app for migration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db.init_app(app)

def migrate_reorder_points():
    """Add reorder point management to existing database"""
    print("Adding Reorder Point Management to Phase 4...")
    print("Setting up automated low stock alerts and reorder suggestions")
    print("-" * 60)
    
    with app.app_context():
        try:
            # Step 1: Verify current state
            print("Step 1: Checking current database state...")
            product_count = Product.query.count()
            transaction_count = StockTransaction.query.count()
            
            print(f"✅ Current database contains:")
            print(f"   - Products: {product_count}")
            print(f"   - Stock Transactions: {transaction_count}")
            
            # Step 2: Create ReorderPoint table
            print("\nStep 2: Creating reorder point management table...")
            db.create_all()  # This will create the ReorderPoint table
            print("✅ ReorderPoint table created successfully")
            
            # Step 3: Create default reorder points for existing products
            print("\nStep 3: Setting up default reorder points for existing products...")
            products_without_reorder = Product.query.outerjoin(ReorderPoint).filter(ReorderPoint.id.is_(None)).all()
            
            created_count = 0
            for product in products_without_reorder:
                # Create intelligent default based on current stock
                current_stock = product.quantity
                
                # Set minimum to 25% of current stock (minimum 5, maximum 20)
                default_minimum = max(5, min(20, int(current_stock * 0.25)))
                
                # Set reorder quantity to replenish to 150% of current stock (minimum 25)
                default_reorder = max(25, int(current_stock * 1.5))
                
                reorder_point = ReorderPoint(
                    product_id=product.id,
                    minimum_quantity=default_minimum,
                    reorder_quantity=default_reorder,
                    is_active=True
                )
                
                db.session.add(reorder_point)
                created_count += 1
            
            db.session.commit()
            
            print(f"✅ Created {created_count} default reorder point configurations")
            
            # Step 4: Verify reorder point table
            print("\nStep 4: Verifying reorder point system...")
            reorder_count = ReorderPoint.query.count()
            active_alerts = ReorderPoint.query.join(Product).filter(
                ReorderPoint.is_active == True,
                Product.quantity < ReorderPoint.minimum_quantity
            ).count()
            
            print(f"✅ ReorderPoint system ready:")
            print(f"   - {reorder_count} reorder configurations")
            print(f"   - {active_alerts} products currently need attention")
            
            # Step 5: Show migration results
            print("\nReorder Point Migration Results:")
            print("=" * 40)
            print("✅ Low stock alert system ready")
            print("✅ Configurable reorder points for all products")
            print("✅ Intelligent default thresholds created")
            print("✅ Foundation for automated suggestions")
            
            print(f"\nNext features available:")
            print("1. View low stock alerts dashboard")
            print("2. Configure custom reorder points per product")
            print("3. Get automated reorder suggestions")
            print("4. Track which products need immediate attention")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            print("Your existing data is safe and unchanged.")
            return False

if __name__ == '__main__':
    success = migrate_reorder_points()
    
    if success:
        print("\n🚨 Reorder Point System Active!")
        print("Your inventory now has intelligent low stock monitoring.")
        print("Check the alerts dashboard to see which products need attention!")
    else:
        print("\n⚠️  Migration encountered issues.")
        print("Please check the errors above and try again.")