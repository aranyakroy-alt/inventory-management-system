from flask import Flask, render_template, request, redirect, url_for, flash
import os
from models import db, Product, Supplier, StockTransaction

def log_stock_transaction(product, quantity_change, transaction_type, reason, user_notes=None):
    """
    Helper function to log stock transactions consistently
    
    Args:
        product: Product object being changed
        quantity_change: Integer change in stock (positive or negative)
        transaction_type: String describing the type of transaction
        reason: Short description of why the change was made
        user_notes: Optional detailed notes
    
    Returns:
        StockTransaction object that was created
    """
    # Capture the before state
    quantity_before = product.quantity
    
    # Apply the change
    product.quantity += quantity_change
    
    # Capture the after state
    quantity_after = product.quantity
    
    # Create the transaction record
    transaction = StockTransaction(
        product_id=product.id,
        transaction_type=transaction_type,
        quantity_change=quantity_change,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        reason=reason,
        user_notes=user_notes
    )
    
    # Add transaction to database session (will be committed with product)
    db.session.add(transaction)
    
    return transaction

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
    """Edit an existing product with transaction logging for quantity changes"""
    # Find the product or return 404 if not found
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            sku = request.form['sku']
            description = request.form['description']
            price = float(request.form['price'])
            new_quantity = int(request.form['quantity'])  # New quantity from form
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
            
            # TRANSACTION LOGGING: Check if quantity changed
            old_quantity = product.quantity
            quantity_changed = new_quantity != old_quantity
            
            if quantity_changed:
                # Calculate the change
                quantity_change = new_quantity - old_quantity
                
                # Validate the new quantity
                if new_quantity < 0:
                    flash(f'Cannot set quantity to {new_quantity} (cannot be negative)', 'error')
                    suppliers = Supplier.query.all()
                    return render_template('edit_product.html', product=product, suppliers=suppliers)
                
                # Create transaction record BEFORE updating the product
                transaction = StockTransaction(
                    product_id=product.id,
                    transaction_type='edit_adjustment',
                    quantity_change=quantity_change,
                    quantity_before=old_quantity,
                    quantity_after=new_quantity,
                    reason=f'Quantity changed via product edit ({old_quantity} → {new_quantity})',
                    user_notes=f'Product "{name}" quantity updated during edit operation'
                )
                
                # Add transaction to session
                db.session.add(transaction)
            
            # Update the product (including quantity)
            product.name = name
            product.sku = sku
            product.description = description
            product.price = price
            product.quantity = new_quantity  # Set the new quantity
            product.supplier_id = supplier_id
            
            # Save to database (commits both product and transaction if any)
            db.session.commit()
            
            # Create appropriate success message
            if quantity_changed:
                if quantity_change > 0:
                    flash(f'Product "{name}" updated successfully! Stock increased by {quantity_change} (was {old_quantity}, now {new_quantity})', 'success')
                else:
                    flash(f'Product "{name}" updated successfully! Stock decreased by {abs(quantity_change)} (was {old_quantity}, now {new_quantity})', 'success')
            else:
                flash(f'Product "{name}" updated successfully!', 'success')
            
            return redirect(url_for('products'))
            
        except ValueError:
            flash('Please enter valid numbers for price and quantity.', 'error')
        except Exception as e:
            db.session.rollback()  # Rollback in case of error
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
    """Adjust product stock quantity with transaction logging"""
    try:
        # Find the product or return 404 if not found
        product = Product.query.get_or_404(id)
        
        # Store current values for messages
        product_name = product.name
        old_quantity = product.quantity
        
        # Determine the change and reason based on action
        if action == 'increase':
            if product.quantity + 1 >= 0:  # Safety check
                transaction = log_stock_transaction(
                    product=product,
                    quantity_change=1,
                    transaction_type='manual_adjustment',
                    reason='Manual increase (+1)',
                    user_notes=f'Stock increased via quick adjustment button'
                )
                
                # Commit both product update and transaction
                db.session.commit()
                
                flash(f'Added 1 to "{product_name}" stock (was {old_quantity}, now {product.quantity})', 'success')
            else:
                flash(f'Cannot increase "{product_name}" stock - calculation error', 'error')
                return redirect(url_for('products'))
                
        elif action == 'decrease':
            if product.quantity > 0:
                transaction = log_stock_transaction(
                    product=product,
                    quantity_change=-1,
                    transaction_type='manual_adjustment',
                    reason='Manual decrease (-1)',
                    user_notes=f'Stock decreased via quick adjustment button'
                )
                
                # Commit both product update and transaction
                db.session.commit()
                
                flash(f'Removed 1 from "{product_name}" stock (was {old_quantity}, now {product.quantity})', 'success')
            else:
                flash(f'Cannot decrease "{product_name}" stock - already at 0', 'error')
                return redirect(url_for('products'))
        else:
            flash('Invalid stock adjustment action', 'error')
            return redirect(url_for('products'))
        
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        flash(f'Error adjusting stock: {str(e)}', 'error')
    
    return redirect(url_for('products'))

@app.route('/bulk_adjust_stock/<int:id>', methods=['POST'])
def bulk_adjust_stock(id):
    """Adjust product stock by custom amount with transaction logging"""
    try:
        # Find the product or return 404 if not found
        product = Product.query.get_or_404(id)
        
        # Get adjustment amount from form
        adjustment = int(request.form.get('adjustment', 0))
        
        if adjustment == 0:
            flash('Please enter a valid adjustment amount', 'error')
            return redirect(url_for('products'))
        
        # Store current values for messages and validation
        product_name = product.name
        old_quantity = product.quantity
        new_quantity = old_quantity + adjustment
        
        # Validate new quantity isn't negative
        if new_quantity < 0:
            flash(f'Cannot adjust "{product_name}" stock to {new_quantity} (would be negative)', 'error')
            return redirect(url_for('products'))
        
        # Determine reason and notes based on adjustment type
        if adjustment > 0:
            reason = f'Bulk increase (+{adjustment})'
            user_notes = f'Stock increased by {adjustment} units via bulk adjustment'
        else:
            reason = f'Bulk decrease ({adjustment})'
            user_notes = f'Stock decreased by {abs(adjustment)} units via bulk adjustment'
        
        # Log the transaction (this also applies the change to product.quantity)
        transaction = log_stock_transaction(
            product=product,
            quantity_change=adjustment,
            transaction_type='manual_adjustment',
            reason=reason,
            user_notes=user_notes
        )
        
        # Commit both product update and transaction
        db.session.commit()
        
        # Create appropriate success message
        if adjustment > 0:
            flash(f'Added {adjustment} to "{product_name}" stock (was {old_quantity}, now {product.quantity})', 'success')
        else:
            flash(f'Removed {abs(adjustment)} from "{product_name}" stock (was {old_quantity}, now {product.quantity})', 'success')
        
    except ValueError:
        flash('Please enter a valid number for stock adjustment', 'error')
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        flash(f'Error adjusting stock: {str(e)}', 'error')
    
    return redirect(url_for('products'))

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

# ADD these routes to your app.py file before "if __name__ == '__main__':"

@app.route('/transactions')
def transactions():
    """Display all stock transactions with filtering options"""
    # Get filter parameters from URL
    product_filter = request.args.get('product_id', '')
    transaction_type = request.args.get('type', 'all')
    
    # Start with base query (most recent first)
    query = StockTransaction.query.order_by(StockTransaction.created_at.desc())
    
    # Apply product filter if specified
    if product_filter and product_filter.isdigit():
        query = query.filter(StockTransaction.product_id == int(product_filter))
    
    # Apply transaction type filter
    if transaction_type != 'all':
        query = query.filter(StockTransaction.transaction_type == transaction_type)
    
    # Execute query and get results
    all_transactions = query.limit(100).all()  # Limit to last 100 transactions
    
    # Get all products for the filter dropdown
    all_products = Product.query.order_by(Product.name).all()
    
    return render_template('transactions.html', 
                         transactions=all_transactions, 
                         products=all_products,
                         selected_product=product_filter,
                         selected_type=transaction_type)

@app.route('/product/<int:id>/history')
def product_history(id):
    """Display stock transaction history for a specific product"""
    # Find the product or return 404
    product = Product.query.get_or_404(id)
    
    # Get all transactions for this product (most recent first)
    transactions = StockTransaction.query.filter_by(product_id=id).order_by(StockTransaction.created_at.desc()).all()
    
    # Calculate some basic statistics
    total_transactions = len(transactions)
    total_increases = sum(1 for t in transactions if t.is_increase)
    total_decreases = sum(1 for t in transactions if t.is_decrease)
    total_quantity_added = sum(t.quantity_change for t in transactions if t.is_increase)
    total_quantity_removed = abs(sum(t.quantity_change for t in transactions if t.is_decrease))
    
    stats = {
        'total_transactions': total_transactions,
        'total_increases': total_increases,
        'total_decreases': total_decreases,
        'total_quantity_added': total_quantity_added,
        'total_quantity_removed': total_quantity_removed
    }
    
    return render_template('product_history.html', 
                         product=product, 
                         transactions=transactions,
                         stats=stats)

# Run the application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)