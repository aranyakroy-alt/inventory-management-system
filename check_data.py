# check_data.py
# See what products are currently in your database

import sqlite3

def check_current_data():
    """Display all current products"""
    try:
        conn = sqlite3.connect('instance/inventory.db')
        cursor = conn.cursor()
        
        # Get all products
        cursor.execute('SELECT * FROM product')
        products = cursor.fetchall()
        
        print(f"Current database contains {len(products)} products:")
        print("-" * 50)
        
        for product in products:
            print(f"ID: {product[0]}")
            print(f"Name: {product[1]}")
            print(f"SKU: {product[2]}")
            print(f"Price: ${product[4]}")
            print(f"Quantity: {product[5]}")
            print("-" * 30)
        
        conn.close()
        return products
        
    except Exception as e:
        print(f"Error checking data: {e}")
        return []

if __name__ == '__main__':
    products = check_current_data()
    
    if not products:
        print("No products found or error occurred.")
    else:
        print(f"\nTotal: {len(products)} products")
        print("This data will be preserved during migration.")