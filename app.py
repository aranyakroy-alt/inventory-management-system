from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Product, Supplier
import os

# Create Flask application
app = Flask(__name__)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Needed for flash messages

# Initialize database with app
db.init_app(app)

# Routes (URL endpoints)
@app.route('/')
def index():
    """Homepage"""
    return render_template('index.html')

@app.route('/products')
def products():
    """Display all products with optional search and filter"""
    search_query = request.args.get('search', '').strip()
    filter_type = request.args.get('filter', 'all')
    
    # Start with base query
    query = Product.query
    
    # Apply search filter if provided
    if search_query:
        query = query.filter(
            Product.name.contains(search_query) |
            Product.sku.contains(search_query) |
            Product.description.contains(search_query)
        )
    
    # Apply stock status filter
    if filter_type == 'in_stock':
        query = query.filter(Product.quantity >= 10)
    elif filter_type == 'low_stock':
        query = query.filter(Product.quantity > 0, Product.quantity < 10)
    elif filter_type == 'out_of_stock':
        query = query.filter(Product.quantity == 0)
    # 'all' or any other value shows all products (no additional filter)
    
    # Execute query
    all_products = query.all()
    
    return render_template('products.html', products=all_products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    """Add a new product"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            sku = request.form['sku']
            description = request.form['description']
            price = float(request.form['price'])
            quantity = int(request.form['quantity'])
            supplier_id = request.form.get('supplier_id')
            
            # Convert empty string to None for supplier_id
            if supplier_id == '':
                supplier_id = None
            else:
                supplier_id = int(supplier_id)
            
            # Create new product
            new_product = Product(
                name=name,
                sku=sku,
                description=description,
                price=price,
                quantity=quantity,
                supplier_id=supplier_id
            )
            
            # Add to database
            db.session.add(new_product)
            db.session.commit()
            
            flash(f'Product "{name}" added successfully!', 'success')
            return redirect(url_for('products'))
            
        except ValueError:
            flash('Please enter valid numbers for price and quantity.', 'error')
        except Exception as e:
            flash(f'Error adding product: {str(e)}', 'error')
    
    # GET request - show the form with suppliers list
    suppliers = Supplier.query.all()
    return render_template('add_product.html', suppliers=suppliers)

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    """Edit an existing product"""
    # Find the product or return 404 if not found
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            sku = request.form['sku']
            description = request.form['description']
            price = float(request.form['price'])
            quantity = int(request.form['quantity'])
            supplier_id = request.form.get('supplier_id')
            
            # Convert empty string to None for supplier_id
            if supplier_id == '':
                supplier_id = None
            else:
                supplier_id = int(supplier_id)
            
            # Check if SKU is unique (excluding current product)
            existing_product = Product.query.filter(Product.sku == sku, Product.id != id).first()
            if existing_product:
                flash(f'SKU "{sku}" is already in use by another product.', 'error')
                suppliers = Supplier.query.all()
                return render_template('edit_product.html', product=product, suppliers=suppliers)
            
            # Update the product
            product.name = name
            product.sku = sku
            product.description = description
            product.price = price
            product.quantity = quantity
            product.supplier_id = supplier_id
            
            # Save to database
            db.session.commit()
            
            flash(f'Product "{name}" updated successfully!', 'success')
            return redirect(url_for('products'))
            
        except ValueError:
            flash('Please enter valid numbers for price and quantity.', 'error')
        except Exception as e:
            flash(f'Error updating product: {str(e)}', 'error')
    
    # GET request - show the edit form with current data and suppliers list
    suppliers = Supplier.query.all()
    return render_template('edit_product.html', product=product, suppliers=suppliers)

@app.route('/delete_product/<int:id>')
def delete_product(id):
    """Delete a product"""
    try:
        # Find the product or return 404 if not found
        product = Product.query.get_or_404(id)
        product_name = product.name  # Store name before deletion for message
        
        # Delete from database
        db.session.delete(product)
        db.session.commit()
        
        flash(f'Product "{product_name}" deleted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error deleting product: {str(e)}', 'error')
    
    return redirect(url_for('products'))

@app.route('/adjust_stock/<int:id>/<action>')
def adjust_stock(id, action):
    """Adjust product stock quantity"""
    try:
        # Find the product or return 404 if not found
        product = Product.query.get_or_404(id)
        
        # Store current values for messages
        product_name = product.name
        old_quantity = product.quantity
        
        # Perform stock adjustment
        if action == 'increase':
            product.quantity += 1
            new_quantity = product.quantity
            flash(f'✅ Added 1 to "{product_name}" stock (was {old_quantity}, now {new_quantity})', 'success')
            
        elif action == 'decrease':
            if product.quantity > 0:
                product.quantity -= 1
                new_quantity = product.quantity
                flash(f'➖ Removed 1 from "{product_name}" stock (was {old_quantity}, now {new_quantity})', 'success')
            else:
                flash(f'❌ Cannot decrease "{product_name}" stock - already at 0', 'error')
                return redirect(url_for('products'))
        else:
            flash('❌ Invalid stock adjustment action', 'error')
            return redirect(url_for('products'))
        
        # Save changes to database
        db.session.commit()
        
    except Exception as e:
        flash(f'❌ Error adjusting stock: {str(e)}', 'error')
    
    return redirect(url_for('products'))

@app.route('/bulk_adjust_stock/<int:id>', methods=['POST'])
def bulk_adjust_stock(id):
    """Adjust product stock by custom amount"""
    try:
        # Find the product or return 404 if not found
        product = Product.query.get_or_404(id)
        
        # Get adjustment amount from form
        adjustment = int(request.form.get('adjustment', 0))
        
        if adjustment == 0:
            flash('❌ Please enter a valid adjustment amount', 'error')
            return redirect(url_for('products'))
        
        # Store current values for messages
        product_name = product.name
        old_quantity = product.quantity
        new_quantity = old_quantity + adjustment
        
        # Validate new quantity isn't negative
        if new_quantity < 0:
            flash(f'❌ Cannot adjust "{product_name}" stock to {new_quantity} (would be negative)', 'error')
            return redirect(url_for('products'))
        
        # Apply adjustment
        product.quantity = new_quantity
        
        # Create appropriate message
        if adjustment > 0:
            flash(f'✅ Added {adjustment} to "{product_name}" stock (was {old_quantity}, now {new_quantity})', 'success')
        else:
            flash(f'➖ Removed {abs(adjustment)} from "{product_name}" stock (was {old_quantity}, now {new_quantity})', 'success')
        
        # Save changes to database
        db.session.commit()
        
    except ValueError:
        flash('❌ Please enter a valid number for stock adjustment', 'error')
    except Exception as e:
        flash(f'❌ Error adjusting stock: {str(e)}', 'error')
    
    return redirect(url_for('products'))

# Add these routes to your app.py file, before the "if __name__ == '__main__':" line

@app.route('/suppliers')
def suppliers():
    """Display all suppliers"""
    all_suppliers = Supplier.query.all()
    return render_template('suppliers.html', suppliers=all_suppliers)

@app.route('/add_supplier', methods=['GET', 'POST'])
def add_supplier():
    """Add a new supplier"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            contact_person = request.form.get('contact_person', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            
            # Validate required fields
            if not name.strip():
                flash('Supplier name is required.', 'error')
                return render_template('add_supplier.html')
            
            # Create new supplier
            new_supplier = Supplier(
                name=name.strip(),
                contact_person=contact_person if contact_person else None,
                email=email if email else None,
                phone=phone if phone else None,
                address=address if address else None
            )
            
            # Add to database
            db.session.add(new_supplier)
            db.session.commit()
            
            flash(f'Supplier "{name}" added successfully!', 'success')
            return redirect(url_for('suppliers'))
            
        except Exception as e:
            flash(f'Error adding supplier: {str(e)}', 'error')
    
    return render_template('add_supplier.html')

@app.route('/edit_supplier/<int:id>', methods=['GET', 'POST'])
def edit_supplier(id):
    """Edit an existing supplier"""
    # Find the supplier or return 404 if not found
    supplier = Supplier.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            contact_person = request.form.get('contact_person', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            
            # Validate required fields
            if not name.strip():
                flash('Supplier name is required.', 'error')
                return render_template('edit_supplier.html', supplier=supplier)
            
            # Update the supplier
            supplier.name = name.strip()
            supplier.contact_person = contact_person if contact_person else None
            supplier.email = email if email else None
            supplier.phone = phone if phone else None
            supplier.address = address if address else None
            
            # Save to database
            db.session.commit()
            
            flash(f'Supplier "{name}" updated successfully!', 'success')
            return redirect(url_for('suppliers'))
            
        except Exception as e:
            flash(f'Error updating supplier: {str(e)}', 'error')
    
    # GET request - show the edit form with current data
    return render_template('edit_supplier.html', supplier=supplier)

@app.route('/delete_supplier/<int:id>')
def delete_supplier(id):
    """Delete a supplier"""
    try:
        # Find the supplier or return 404 if not found
        supplier = Supplier.query.get_or_404(id)
        
        # Check if supplier has products
        product_count = len(supplier.products)
        if product_count > 0:
            flash(f'Cannot delete "{supplier.name}" - it has {product_count} products assigned. Remove products first.', 'error')
            return redirect(url_for('suppliers'))
        
        supplier_name = supplier.name  # Store name before deletion
        
        # Delete from database
        db.session.delete(supplier)
        db.session.commit()
        
        flash(f'Supplier "{supplier_name}" deleted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error deleting supplier: {str(e)}', 'error')
    
    return redirect(url_for('suppliers'))

# Run the application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)