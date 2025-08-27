# fixed_migration.py
# Properly handles SQLite's limitations when adding columns

from flask import Flask
from models import db, Product, Supplier
import sqlite3
import os

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db.init_app(app)

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    try:
        conn = sqlite3.connect('instance/inventory.db')
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        conn.close()
        return column_name in columns
    except Exception as e:
        print(f"Error checking column: {e}")
        return False

def add_supplier_column():
    """Add supplier_id column to existing product table"""
    try:
        conn = sqlite3.connect('instance/inventory.db')
        cursor = conn.cursor()
        
        # Add the supplier_id column
        cursor.execute('ALTER TABLE product ADD COLUMN supplier_id INTEGER')
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column already exists, skipping...")
            return True
        else:
            print(f"Error adding column: {e}")
            return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def migrate_database():
    """Complete migration process"""
    print("Starting database migration...")
    
    with app.app_context():
        try:
            # Step 1: Create any new tables (like supplier)
            print("Step 1: Creating new tables...")
            db.create_all()
            print("- Supplier table created (if it didn't exist)")
            
            # Step 2: Check if supplier_id column exists in product table
            print("Step 2: Checking product table structure...")
            if not check_column_exists('product', 'supplier_id'):
                print("- supplier_id column missing, adding it...")
                if add_supplier_column():
                    print("- supplier_id column added successfully")
                else:
                    print("- Failed to add supplier_id column")
                    return False
            else:
                print("- supplier_id column already exists")
            
            # Step 3: Verify everything works
            print("Step 3: Testing the migration...")
            product_count = Product.query.count()
            supplier_count = Supplier.query.count()
            
            print(f"Migration completed successfully!")
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
        print("\nDatabase is ready for Phase 3!")
        print("You can now continue with supplier management features.")
    else:
        print("\nMigration failed. Please check the errors above.")
        print("Your original data is still safe in the backup.")