from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Product
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
    """Display all products"""
    all_products = Product.query.all()
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
            
            # Create new product
            new_product = Product(
                name=name,
                sku=sku,
                description=description,
                price=price,
                quantity=quantity
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
    
    return render_template('add_product.html')

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
            
            # Check if SKU is unique (excluding current product)
            existing_product = Product.query.filter(Product.sku == sku, Product.id != id).first()
            if existing_product:
                flash(f'SKU "{sku}" is already in use by another product.', 'error')
                return render_template('edit_product.html', product=product)
            
            # Update the product
            product.name = name
            product.sku = sku
            product.description = description
            product.price = price
            product.quantity = quantity
            
            # Save to database
            db.session.commit()
            
            flash(f'Product "{name}" updated successfully!', 'success')
            return redirect(url_for('products'))
            
        except ValueError:
            flash('Please enter valid numbers for price and quantity.', 'error')
        except Exception as e:
            flash(f'Error updating product: {str(e)}', 'error')
    
    # GET request - show the edit form with current data
    return render_template('edit_product.html', product=product)

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

# Run the application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)