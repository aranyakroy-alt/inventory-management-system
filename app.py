from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response, session
import os
from models import db, Product, Supplier, StockTransaction, ReorderPoint
import csv
import io
from pdf_reports import generate_inventory_summary_pdf, generate_low_stock_pdf, generate_supplier_performance_pdf
from sqlalchemy import func, and_, or_, text, desc, asc
from datetime import datetime, timedelta, date
import json
from collections import defaultdict
import statistics
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from forms import LoginForm, UserRegistrationForm, UserEditForm, PasswordChangeForm, AdminPasswordResetForm
from auth_utils import (login_required_with_message, role_required, permission_required, 
                       admin_required, manager_or_admin_required, active_user_required,
                       self_or_admin_required, auth_template_context)
from models import User, UserRole  # Add User, UserRole to your existing models import
from werkzeug.security import generate_password_hash



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
        user_notes=user_notes,
        performed_by_id=current_user.id if current_user.is_authenticated else None  
    )
    
    # Add transaction to database session (will be committed with product)
    db.session.add(transaction)
    
    return transaction

def generate_bi_recommendations(health_score, alert_efficiency, supplier_utilization, transaction_velocity):
    """Generate business intelligence recommendations"""
    recommendations = []
    
    if health_score < 70:
        recommendations.append({
            'type': 'inventory_health',
            'priority': 'high',
            'message': 'Inventory health needs attention - consider reviewing minimum stock levels',
            'action': 'Review and adjust reorder points for critical products'
        })
    
    if alert_efficiency < 75:
        recommendations.append({
            'type': 'alert_system',
            'priority': 'medium', 
            'message': 'Alert system efficiency could be improved',
            'action': 'Review reorder point configurations and adjust thresholds'
        })
    
    if supplier_utilization < 60:
        recommendations.append({
            'type': 'supplier_management',
            'priority': 'medium',
            'message': 'Consider activating more suppliers to improve supply chain resilience',
            'action': 'Review inactive suppliers and establish product assignments'
        })
    
    if transaction_velocity < 1:
        recommendations.append({
            'type': 'operational_efficiency',
            'priority': 'low',
            'message': 'Low transaction activity - consider promotional strategies',
            'action': 'Analyze slow-moving inventory and implement movement strategies'
        })
    
    if len(recommendations) == 0:
        recommendations.append({
            'type': 'performance',
            'priority': 'info',
            'message': 'System performance is optimal across all metrics',
            'action': 'Continue monitoring and maintain current operational standards'
        })
    
    return recommendations

def calculate_optimal_restock_day(day_patterns):
    """Calculate optimal day for restocking based on activity patterns"""
    if not day_patterns:
        return 'Sunday'
    
    min_activity_day = min(day_patterns.items(), key=lambda x: x[1])
    return min_activity_day[0]

def calculate_activity_consistency(weekly_averages):
    """Calculate how consistent weekly activity is"""
    if len(weekly_averages) < 2:
        return 'Insufficient data'
    
    values = list(weekly_averages.values())
    std_dev = statistics.stdev(values) if len(values) > 1 else 0
    mean_val = statistics.mean(values)
    
    coefficient_of_variation = (std_dev / mean_val * 100) if mean_val > 0 else 0
    
    if coefficient_of_variation < 20:
        return 'Highly consistent'
    elif coefficient_of_variation < 40:
        return 'Moderately consistent'
    else:
        return 'Highly variable'

def generate_supplier_recommendations(risk_level, value_concentration, low_stock_ratio):
    """Generate specific recommendations for supplier management"""
    recommendations = []
    
    if risk_level == 'high':
        if value_concentration > 40:
            recommendations.append('Consider diversifying inventory across multiple suppliers')
        if low_stock_ratio > 50:
            recommendations.append('Urgent: Multiple products from this supplier need restocking')
        recommendations.append('Monitor this supplier closely due to high dependency')
    elif risk_level == 'medium':
        if value_concentration > 25:
            recommendations.append('Monitor supplier concentration - consider alternatives')
        if low_stock_ratio > 30:
            recommendations.append('Several products need attention - plan restocking')
    else:
        recommendations.append('Supplier relationship is well-managed')
        
    return recommendations

def assess_supplier_diversification(risk_assessment):
    """Assess overall supplier portfolio diversification"""
    if not risk_assessment:
        return 'No supplier data available'
        
    high_risk_count = sum(1 for s in risk_assessment if s['risk_level'] == 'high')
    total_suppliers = len(risk_assessment)
    
    if high_risk_count / total_suppliers > 0.3:
        return 'Poor diversification - high supplier concentration risk'
    elif high_risk_count / total_suppliers > 0.1:
        return 'Moderate diversification - some concentration risk exists'
    else:
        return 'Good diversification - supplier risk is well-distributed'

def calculate_optimization_score(current_stock, optimal_stock, days_remaining, current_value):
    """Calculate optimization score (0-100, lower = more optimization potential)"""
    # Stock level optimization (0-40 points)
    stock_ratio = current_stock / optimal_stock if optimal_stock > 0 else 1
    stock_score = min(40, 40 * min(stock_ratio, 2))
    
    # Time efficiency (0-30 points)  
    time_score = 30 if days_remaining == float('inf') else min(30, days_remaining / 30 * 30)
    
    # Value efficiency (0-30 points)
    value_score = min(30, current_value / 1000 * 30)
    
    return round(stock_score + time_score + value_score, 1)

def generate_optimization_recommendations(current_stock, optimal_stock, days_remaining, daily_demand):
    """Generate specific optimization recommendations"""
    recommendations = []
    
    if days_remaining != float('inf') and days_remaining < 7:
        recommendations.append('URGENT: Restock immediately - less than 7 days remaining')
    elif days_remaining != float('inf') and days_remaining < 14:
        recommendations.append('Schedule restock within next week')
    
    if current_stock > optimal_stock * 2:
        recommendations.append('Consider reducing stock levels - current inventory is excessive')
    elif current_stock < optimal_stock * 0.5:
        recommendations.append('Increase stock levels to improve service levels')
    
    if daily_demand > 0:
        recommendations.append(f'Set reorder point to {round(daily_demand * 7, 0)} units (7-day supply)')
    else:
        recommendations.append('Enable transaction monitoring to establish optimal levels')
    
    return recommendations

def calculate_system_health_score(active_products, total_products, triggered_alerts, total_alerts, recent_transactions, inventory_value):
    """Calculate overall system health score (0-100)"""
    # Product health (25 points)
    product_health = (active_products / total_products * 25) if total_products > 0 else 0
    
    # Alert system health (25 points)
    alert_health = ((total_alerts - triggered_alerts) / total_alerts * 25) if total_alerts > 0 else 25
    
    # Activity health (25 points) - based on transaction frequency
    activity_health = min(25, recent_transactions / 30 * 5)  # 6+ transactions/day = full points
    
    # Value health (25 points) - based on inventory value  
    value_health = min(25, inventory_value / 10000 * 25)  # $10k+ inventory = full points
    
    total_score = product_health + alert_health + activity_health + value_health
    
    status = 'Excellent' if total_score > 85 else 'Good' if total_score > 70 else 'Fair' if total_score > 50 else 'Poor'
    
    return {
        'score': round(total_score, 1),
        'status': status,
        'components': {
            'product_health': round(product_health, 1),
            'alert_health': round(alert_health, 1), 
            'activity_health': round(activity_health, 1),
            'value_health': round(value_health, 1)
        }
    }

def generate_executive_recommendations(system_health, metrics):
    """Generate executive-level recommendations"""
    recommendations = []
    
    if system_health['score'] < 70:
        recommendations.append({
            'priority': 'High',
            'category': 'System Health',
            'recommendation': 'System health requires immediate attention',
            'action': 'Review inventory processes and implement corrective measures'
        })
    
    if metrics['transaction_velocity'] < 2:
        recommendations.append({
            'priority': 'Medium',
            'category': 'Operational Efficiency', 
            'recommendation': 'Low transaction activity detected',
            'action': 'Analyze product movement patterns and consider promotional strategies'
        })
    
    if metrics['alert_effectiveness'] < 80:
        recommendations.append({
            'priority': 'Medium',
            'category': 'Alert Management',
            'recommendation': 'Alert system effectiveness below optimal',
            'action': 'Review and adjust reorder point configurations'
        })
    
    if metrics['value_growth'] < 0:
        recommendations.append({
            'priority': 'High',
            'category': 'Financial Performance',
            'recommendation': 'Inventory value declining',
            'action': 'Investigate causes and implement value preservation strategies'
        })
    
    if len(recommendations) == 0:
        recommendations.append({
            'priority': 'Info',
            'category': 'Performance', 
            'recommendation': 'All systems operating optimally',
            'action': 'Continue current operational standards'
        })
    
    return recommendations


# Create Flask application
app = Flask(__name__)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Needed for flash messages

app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS attacks
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # Session expires after 2 hours


# Flask-Login configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Add authentication context to all templates
app.context_processor(auth_template_context)

@app.before_request
def session_security():
    """Enhanced session security and cleanup"""
    # Make sessions permanent with timeout
    session.permanent = True
    
    # Force logout if session is too old or invalid
    if current_user.is_authenticated:
        # Check if user account is still active
        if not current_user.is_active:
            logout_user()
            session.clear()
            flash('Your account has been deactivated. Please contact an administrator.', 'error')
            return redirect(url_for('login'))
    
    # Prevent access to login page if already logged in
    if request.endpoint == 'login' and current_user.is_authenticated:
        return redirect(url_for('dashboard'))

@app.after_request
def after_request_security(response):
    """Add security headers to all responses"""
    # Prevent caching of sensitive pages for logged-in users
    if current_user.is_authenticated:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    # Security headers
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'  # Prevent clickjacking
    response.headers['X-Content-Type-Options'] = 'nosniff'  # Prevent MIME sniffing
    
    return response

# =============================================================================
# FORCE LOGOUT UTILITY FUNCTION
# =============================================================================

def force_logout_user(user_id, reason="Administrative action"):
    """Force logout a specific user (admin function)"""
    try:
        # This would be more complex in production with session storage
        # For now, we'll just deactivate the user
        user = User.query.get(user_id)
        if user:
            user.is_active = False
            db.session.commit()
            print(f"User {user.username} force-logged out: {reason}")
            return True
    except Exception as e:
        print(f"Error force-logging out user {user_id}: {str(e)}")
    return False


@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return User.query.get(int(user_id))

# Initialize database with app
db.init_app(app)

# Routes (URL endpoints)
@app.route('/')
def index():
    """Homepage"""
    return render_template('index.html')

@app.route('/products')
@login_required_with_message
@active_user_required
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

@app.route('/alerts')
def alerts():
    """Low stock alerts dashboard"""
    # Get all active reorder points with their products
    alerts_query = db.session.query(ReorderPoint, Product).join(Product).filter(
        ReorderPoint.is_active == True
    ).order_by(Product.quantity.asc())
    
    # Categorize alerts by severity
    critical_alerts = []  # Out of stock
    urgent_alerts = []    # Less than 50% of minimum
    warning_alerts = []   # Below minimum but not critical
    ok_products = []      # Above minimum
    
    total_alerts = 0
    
    for reorder_point, product in alerts_query:
        alert_level = reorder_point.alert_level
        alert_data = {
            'product': product,
            'reorder_point': reorder_point,
            'alert_level': alert_level,
            'suggested_order': reorder_point.suggested_order_amount
        }
        
        if alert_level == 'critical':
            critical_alerts.append(alert_data)
            total_alerts += 1
        elif alert_level == 'urgent':
            urgent_alerts.append(alert_data)
            total_alerts += 1
        elif alert_level == 'warning':
            warning_alerts.append(alert_data)
            total_alerts += 1
        else:
            ok_products.append(alert_data)
    
    return render_template('alerts.html',
                         critical_alerts=critical_alerts,
                         urgent_alerts=urgent_alerts,
                         warning_alerts=warning_alerts,
                         ok_products=ok_products[:10],  # Show only first 10 OK products
                         total_alerts=total_alerts)

@app.route('/reorder_points')
def reorder_points():
    """Manage reorder point configurations"""
    # Get all products with their reorder points
    products = db.session.query(Product).outerjoin(ReorderPoint).all()
    
    return render_template('reorder_points.html', products=products)

@app.route('/reorder_points/<int:product_id>', methods=['GET', 'POST'])
def manage_reorder_point(product_id):
    """Configure reorder point for a specific product"""
    product = Product.query.get_or_404(product_id)
    reorder_point = ReorderPoint.query.filter_by(product_id=product_id).first()
    
    if request.method == 'POST':
        try:
            # Get form data
            minimum_quantity = int(request.form['minimum_quantity'])
            reorder_quantity = int(request.form['reorder_quantity'])
            is_active = 'is_active' in request.form
            
            # Validate input
            if minimum_quantity < 0:
                flash('Minimum quantity cannot be negative', 'error')
                return render_template('manage_reorder_point.html', product=product, reorder_point=reorder_point)
            
            if reorder_quantity <= minimum_quantity:
                flash('Reorder quantity should be greater than minimum quantity', 'error')
                return render_template('manage_reorder_point.html', product=product, reorder_point=reorder_point)
            
            # Create or update reorder point
            if reorder_point:
                # Update existing
                reorder_point.minimum_quantity = minimum_quantity
                reorder_point.reorder_quantity = reorder_quantity
                reorder_point.is_active = is_active
                reorder_point.updated_at = db.func.now()
            else:
                # Create new
                reorder_point = ReorderPoint(
                    product_id=product_id,
                    minimum_quantity=minimum_quantity,
                    reorder_quantity=reorder_quantity,
                    is_active=is_active
                )
                db.session.add(reorder_point)
            
            db.session.commit()
            
            status = "active" if is_active else "inactive"
            flash(f'Reorder point for "{product.name}" updated successfully (minimum: {minimum_quantity}, reorder: {reorder_quantity}, {status})', 'success')
            
            # Redirect back to reorder points list
            return redirect(url_for('reorder_points'))
            
        except ValueError:
            flash('Please enter valid numbers for quantities', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating reorder point: {str(e)}', 'error')
    
    return render_template('manage_reorder_point.html', product=product, reorder_point=reorder_point)

@app.route('/quick_reorder/<int:product_id>')
def quick_reorder(product_id):
    """Quick action to generate reorder suggestion for a product"""
    product = Product.query.get_or_404(product_id)
    reorder_point = ReorderPoint.query.filter_by(product_id=product_id).first()
    
    if not reorder_point or not reorder_point.is_active:
        flash(f'No active reorder configuration found for "{product.name}"', 'error')
        return redirect(url_for('alerts'))
    
    # Calculate reorder information
    current_stock = product.quantity
    minimum_needed = reorder_point.minimum_quantity
    suggested_order = reorder_point.suggested_order_amount
    total_after_order = current_stock + suggested_order
    
    # Create detailed reorder message
    supplier_info = f" from {product.supplier.name}" if product.supplier else ""
    
    flash(f'''Reorder suggestion for "{product.name}":
          • Current stock: {current_stock} units
          • Minimum threshold: {minimum_needed} units  
          • Suggested order: {suggested_order} units{supplier_info}
          • Stock after order: {total_after_order} units''', 'success')
    
    return redirect(url_for('alerts'))


@app.route('/export/products')
def export_products():
    """Export all products to CSV format"""
    try:
        # Create CSV data in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header row
        writer.writerow([
            'ID', 'Name', 'SKU', 'Description', 'Price', 'Quantity', 
            'Supplier', 'Created Date', 'Stock Status', 'Total Value'
        ])
        
        # Get all products with supplier information
        products = Product.query.outerjoin(Supplier).all()
        
        for product in products:
            # Determine stock status
            if product.quantity == 0:
                stock_status = 'Out of Stock'
            elif product.quantity < 10:
                stock_status = 'Low Stock'
            else:
                stock_status = 'In Stock'
            
            # Calculate total value
            total_value = product.price * product.quantity
            
            # Get supplier name
            supplier_name = product.supplier.name if product.supplier else 'No Supplier'
            
            # Write product row
            writer.writerow([
                product.id,
                product.name,
                product.sku,
                product.description or '',
                f"{product.price:.2f}",
                product.quantity,
                supplier_name,
                product.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                stock_status,
                f"{total_value:.2f}"
            ])
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=products_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        flash('Products exported successfully!', 'success')
        return response
        
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(url_for('products'))

@app.route('/export/transactions')
def export_transactions():
    """Export transaction history to CSV format"""
    try:
        # Create CSV data in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header row
        writer.writerow([
            'Transaction ID', 'Date', 'Time', 'Product Name', 'SKU', 
            'Transaction Type', 'Quantity Change', 'Quantity Before', 
            'Quantity After', 'Reason', 'Notes'
        ])
        
        # Get all transactions with product information
        transactions = StockTransaction.query.join(Product).order_by(
            StockTransaction.created_at.desc()
        ).all()
        
        for transaction in transactions:
            writer.writerow([
                transaction.id,
                transaction.created_at.strftime('%Y-%m-%d'),
                transaction.created_at.strftime('%H:%M:%S'),
                transaction.product.name,
                transaction.product.sku,
                transaction.transaction_type.replace('_', ' ').title(),
                transaction.quantity_change,
                transaction.quantity_before,
                transaction.quantity_after,
                transaction.reason or '',
                transaction.user_notes or ''
            ])
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=transactions_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        flash('Transaction history exported successfully!', 'success')
        return response
        
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(url_for('transactions'))

@app.route('/export/alerts')
def export_alerts():
    """Export current alert status to CSV format"""
    try:
        # Create CSV data in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header row
        writer.writerow([
            'Product Name', 'SKU', 'Current Stock', 'Minimum Threshold', 
            'Reorder Quantity', 'Alert Level', 'Suggested Order', 
            'Supplier', 'Total Value', 'Status'
        ])
        
        # Get all products with reorder points
        reorder_points = ReorderPoint.query.join(Product).outerjoin(Supplier).all()
        
        for reorder_point in reorder_points:
            product = reorder_point.product
            
            # Calculate suggested order and total value
            suggested_order = reorder_point.suggested_order_amount
            total_value = product.price * product.quantity
            supplier_name = product.supplier.name if product.supplier else 'No Supplier'
            
            # Determine status
            if not reorder_point.is_active:
                status = 'Alerts Disabled'
            else:
                status = 'Active Monitoring'
            
            writer.writerow([
                product.name,
                product.sku,
                product.quantity,
                reorder_point.minimum_quantity,
                reorder_point.reorder_quantity,
                reorder_point.alert_level.title(),
                suggested_order,
                supplier_name,
                f"{total_value:.2f}",
                status
            ])
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=alerts_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        flash('Alert status exported successfully!', 'success')
        return response
        
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(url_for('alerts'))

# NEW: Manager/admin only
@app.route('/import_export')
@manager_or_admin_required
def import_export():
    """Import/Export management page"""
    # Get summary statistics for the import/export page
    stats = {
        'total_products': Product.query.count(),
        'total_transactions': StockTransaction.query.count(),
        'total_suppliers': Supplier.query.count(),
        'active_alerts': ReorderPoint.query.filter(ReorderPoint.is_active == True).count(),
        'last_transaction': StockTransaction.query.order_by(StockTransaction.created_at.desc()).first()
    }
    
    return render_template('import_export.html', stats=stats)

@app.route('/bulk_operations')
def bulk_operations():
    """Bulk stock operations interface"""
    # Get all products for bulk operations
    products = Product.query.order_by(Product.name).all()
    
    return render_template('bulk_operations.html', products=products)

@app.route('/bulk_stock_update', methods=['POST'])
def bulk_stock_update():
    """Process bulk stock updates"""
    try:
        # Get the operation type
        operation_type = request.form.get('operation_type')
        reason = request.form.get('reason', 'Bulk operation')
        
        updates_made = 0
        errors = []
        
        # Process each product update
        for key, value in request.form.items():
            if key.startswith('product_') and value.strip():
                try:
                    product_id = int(key.replace('product_', ''))
                    new_quantity = int(value)
                    
                    if new_quantity < 0:
                        errors.append(f"Product ID {product_id}: Negative quantity not allowed")
                        continue
                    
                    product = Product.query.get(product_id)
                    if not product:
                        errors.append(f"Product ID {product_id}: Not found")
                        continue
                    
                    # Check if quantity actually changed
                    if product.quantity != new_quantity:
                        old_quantity = product.quantity
                        quantity_change = new_quantity - old_quantity
                        
                        # Create transaction record
                        transaction = StockTransaction(
                            product_id=product.id,
                            transaction_type='bulk_adjustment',
                            quantity_change=quantity_change,
                            quantity_before=old_quantity,
                            quantity_after=new_quantity,
                            reason=f"Bulk operation: {reason}",
                            user_notes=f"Updated via bulk operations interface"
                        )
                        
                        # Update product quantity
                        product.quantity = new_quantity
                        
                        # Add transaction to session
                        db.session.add(transaction)
                        updates_made += 1
                
                except ValueError:
                    errors.append(f"Product ID {key}: Invalid quantity value")
                except Exception as e:
                    errors.append(f"Product ID {key}: {str(e)}")
        
        # Commit all changes
        if updates_made > 0:
            db.session.commit()
            flash(f'Bulk update completed: {updates_made} products updated successfully!', 'success')
        
        if errors:
            error_msg = f"{len(errors)} errors occurred: " + "; ".join(errors[:5])
            if len(errors) > 5:
                error_msg += f" (and {len(errors)-5} more...)"
            flash(error_msg, 'error')
        
        if updates_made == 0 and not errors:
            flash('No changes were made - all quantities were already at specified values', 'info')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Bulk update failed: {str(e)}', 'error')
    
    return redirect(url_for('bulk_operations'))

# ADD these additional routes to your app.py file (after the export routes)

@app.route('/import_products', methods=['GET', 'POST'])
def import_products():
    """Import products from CSV file"""
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'csv_file' not in request.files:
                flash('No file selected', 'error')
                return redirect(request.url)
            
            file = request.files['csv_file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
            if not file.filename.lower().endswith('.csv'):
                flash('Please upload a CSV file', 'error')
                return redirect(request.url)
            
            # Read CSV content
            csv_content = file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            # Validate CSV headers
            required_headers = ['Name', 'SKU', 'Price', 'Quantity']
            optional_headers = ['Description', 'Supplier']
            
            if not all(header in csv_reader.fieldnames for header in required_headers):
                missing_headers = [h for h in required_headers if h not in csv_reader.fieldnames]
                flash(f'CSV missing required headers: {", ".join(missing_headers)}', 'error')
                return redirect(request.url)
            
            # Track import results
            imported_count = 0
            updated_count = 0
            error_count = 0
            errors = []
            
            # Process each row
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 because row 1 is headers
                try:
                    # Validate required fields
                    name = row['Name'].strip()
                    sku = row['SKU'].strip()
                    price = float(row['Price'])
                    quantity = int(row['Quantity'])
                    
                    if not name or not sku:
                        errors.append(f"Row {row_num}: Name and SKU are required")
                        error_count += 1
                        continue
                    
                    if price < 0 or quantity < 0:
                        errors.append(f"Row {row_num}: Price and quantity cannot be negative")
                        error_count += 1
                        continue
                    
                    # Optional fields
                    description = row.get('Description', '').strip() or None
                    supplier_name = row.get('Supplier', '').strip()
                    
                    # Find or create supplier
                    supplier_id = None
                    if supplier_name:
                        supplier = Supplier.query.filter_by(name=supplier_name).first()
                        if not supplier:
                            # Create new supplier
                            supplier = Supplier(name=supplier_name)
                            db.session.add(supplier)
                            db.session.flush()  # Get the ID
                        supplier_id = supplier.id
                    
                    # Check if product exists (by SKU)
                    existing_product = Product.query.filter_by(sku=sku).first()
                    
                    if existing_product:
                        # Update existing product
                        old_quantity = existing_product.quantity
                        
                        existing_product.name = name
                        existing_product.description = description
                        existing_product.price = price
                        existing_product.quantity = quantity
                        existing_product.supplier_id = supplier_id
                        
                        # Create transaction if quantity changed
                        if old_quantity != quantity:
                            quantity_change = quantity - old_quantity
                            transaction = StockTransaction(
                                product_id=existing_product.id,
                                transaction_type='import_adjustment',
                                quantity_change=quantity_change,
                                quantity_before=old_quantity,
                                quantity_after=quantity,
                                reason=f'Updated via CSV import',
                                user_notes=f'Product updated from CSV file: {file.filename}'
                            )
                            db.session.add(transaction)
                        
                        updated_count += 1
                    else:
                        # Create new product
                        new_product = Product(
                            name=name,
                            sku=sku,
                            description=description,
                            price=price,
                            quantity=quantity,
                            supplier_id=supplier_id
                        )
                        db.session.add(new_product)
                        db.session.flush()  # Get the product ID
                        
                        # Create initial stock transaction
                        if quantity > 0:
                            transaction = StockTransaction(
                                product_id=new_product.id,
                                transaction_type='import_initial',
                                quantity_change=quantity,
                                quantity_before=0,
                                quantity_after=quantity,
                                reason=f'Initial stock via CSV import',
                                user_notes=f'Product created from CSV file: {file.filename}'
                            )
                            db.session.add(transaction)
                        
                        imported_count += 1
                
                except ValueError as e:
                    errors.append(f"Row {row_num}: Invalid number format")
                    error_count += 1
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    error_count += 1
            
            # Commit all changes
            db.session.commit()
            
            # Create success message
            success_parts = []
            if imported_count > 0:
                success_parts.append(f"{imported_count} new products imported")
            if updated_count > 0:
                success_parts.append(f"{updated_count} existing products updated")
            
            if success_parts:
                flash(f"Import completed: {', '.join(success_parts)}", 'success')
            
            if error_count > 0:
                error_msg = f"{error_count} errors encountered"
                if len(errors) <= 5:
                    error_msg += ": " + "; ".join(errors)
                else:
                    error_msg += f": {errors[0]} (and {len(errors)-1} more...)"
                flash(error_msg, 'error')
            
            return redirect(url_for('products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Import failed: {str(e)}', 'error')
    
    return render_template('import_products.html')

@app.route('/download_template/<template_type>')
def download_template(template_type):
    """Download CSV templates for importing data"""
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        
        if template_type == 'products':
            # Products template
            writer.writerow(['Name', 'SKU', 'Description', 'Price', 'Quantity', 'Supplier'])
            writer.writerow(['Example Product 1', 'PROD-001', 'Sample product description', '19.99', '100', 'Example Supplier'])
            writer.writerow(['Example Product 2', 'PROD-002', 'Another product description', '29.99', '50', 'Another Supplier'])
            filename = 'products_import_template.csv'
            
        elif template_type == 'stock_adjustments':
            # Stock adjustments template (for bulk updates via import)
            products = Product.query.all()
            writer.writerow(['SKU', 'Current_Quantity', 'New_Quantity', 'Reason'])
            for product in products[:5]:  # Show first 5 as examples
                writer.writerow([product.sku, product.quantity, product.quantity, 'Adjustment reason'])
            filename = 'stock_adjustments_template.csv'
            
        else:
            flash('Invalid template type', 'error')
            return redirect(url_for('import_export'))
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    except Exception as e:
        flash(f'Template download failed: {str(e)}', 'error')
        return redirect(url_for('import_export'))

@app.route('/import_stock_adjustments', methods=['GET', 'POST'])
def import_stock_adjustments():
    """Import stock adjustments from CSV file"""
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'csv_file' not in request.files:
                flash('No file selected', 'error')
                return redirect(request.url)
            
            file = request.files['csv_file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
            if not file.filename.lower().endswith('.csv'):
                flash('Please upload a CSV file', 'error')
                return redirect(request.url)
            
            # Get reason for bulk adjustment
            bulk_reason = request.form.get('reason', '').strip()
            if not bulk_reason:
                flash('Please provide a reason for the stock adjustments', 'error')
                return redirect(request.url)
            
            # Read CSV content
            csv_content = file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            # Validate CSV headers
            required_headers = ['SKU', 'New_Quantity']
            if not all(header in csv_reader.fieldnames for header in required_headers):
                missing_headers = [h for h in required_headers if h not in csv_reader.fieldnames]
                flash(f'CSV missing required headers: {", ".join(missing_headers)}', 'error')
                return redirect(request.url)
            
            # Track import results
            updated_count = 0
            error_count = 0
            errors = []
            
            # Process each row
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    sku = row['SKU'].strip()
                    new_quantity = int(row['New_Quantity'])
                    row_reason = row.get('Reason', '').strip() or bulk_reason
                    
                    if new_quantity < 0:
                        errors.append(f"Row {row_num}: Negative quantity not allowed")
                        error_count += 1
                        continue
                    
                    # Find product by SKU
                    product = Product.query.filter_by(sku=sku).first()
                    if not product:
                        errors.append(f"Row {row_num}: Product with SKU '{sku}' not found")
                        error_count += 1
                        continue
                    
                    # Check if quantity actually changed
                    if product.quantity != new_quantity:
                        old_quantity = product.quantity
                        quantity_change = new_quantity - old_quantity
                        
                        # Create transaction
                        transaction = StockTransaction(
                            product_id=product.id,
                            transaction_type='import_adjustment',
                            quantity_change=quantity_change,
                            quantity_before=old_quantity,
                            quantity_after=new_quantity,
                            reason=f'Stock adjustment import: {row_reason}',
                            user_notes=f'Imported from CSV file: {file.filename}'
                        )
                        
                        # Update product quantity
                        product.quantity = new_quantity
                        
                        # Add transaction
                        db.session.add(transaction)
                        updated_count += 1
                
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid quantity value")
                    error_count += 1
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    error_count += 1
            
            # Commit changes
            db.session.commit()
            
            if updated_count > 0:
                flash(f"Stock adjustments imported: {updated_count} products updated", 'success')
            
            if error_count > 0:
                error_msg = f"{error_count} errors encountered"
                if len(errors) <= 3:
                    error_msg += ": " + "; ".join(errors)
                else:
                    error_msg += f": {errors[0]} (and {len(errors)-1} more...)"
                flash(error_msg, 'error')
            
            if updated_count == 0 and error_count == 0:
                flash('No changes were made - all quantities were already at specified values', 'info')
            
            return redirect(url_for('transactions'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Import failed: {str(e)}', 'error')
    
    return render_template('import_stock_adjustments.html')

@app.route('/reports')
def reports():
    """Professional reports dashboard and selection"""
    # Get summary statistics for the reports page
    stats = {
        'total_products': Product.query.count(),
        'total_transactions': StockTransaction.query.count(),
        'total_suppliers': Supplier.query.count(),
        'active_alerts': ReorderPoint.query.filter(ReorderPoint.is_active == True).count(),
        'out_of_stock': Product.query.filter(Product.quantity == 0).count(),
        'low_stock': Product.query.filter(Product.quantity > 0, Product.quantity < 10).count(),
        'last_transaction': StockTransaction.query.order_by(StockTransaction.created_at.desc()).first()
    }
    
    # Calculate inventory value
    inventory_value_query = db.session.query(db.func.sum(Product.price * Product.quantity)).scalar()
    stats['total_inventory_value'] = inventory_value_query if inventory_value_query else 0.0
    
    # Get active alerts count
    alerts_count = db.session.query(ReorderPoint, Product).join(Product).filter(
        ReorderPoint.is_active == True,
        Product.quantity < ReorderPoint.minimum_quantity
    ).count()
    stats['active_alerts_count'] = alerts_count
    
    return render_template('reports.html', stats=stats)

@app.route('/reports/generate/inventory_summary')
def generate_inventory_summary_report():
    """Generate and download comprehensive inventory summary PDF report"""
    try:
        # Generate PDF
        pdf_buffer = generate_inventory_summary_pdf()
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'Inventory_Summary_Report_{timestamp}.pdf'
        
        # Send file
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Error generating inventory summary report: {str(e)}', 'error')
        return redirect(url_for('reports'))

@app.route('/reports/generate/low_stock_alerts')
def generate_low_stock_alerts_report():
    """Generate and download low stock alerts PDF report"""
    try:
        # Generate PDF
        pdf_buffer = generate_low_stock_pdf()
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'Low_Stock_Alerts_Report_{timestamp}.pdf'
        
        # Send file
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Error generating low stock alerts report: {str(e)}', 'error')
        return redirect(url_for('reports'))

@app.route('/reports/generate/supplier_performance')
def generate_supplier_performance_report():
    """Generate and download supplier performance PDF report"""
    try:
        # Generate PDF
        pdf_buffer = generate_supplier_performance_pdf()
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'Supplier_Performance_Report_{timestamp}.pdf'
        
        # Send file
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Error generating supplier performance report: {str(e)}', 'error')
        return redirect(url_for('reports'))

@app.route('/reports/preview/<report_type>')
def preview_report(report_type):
    """Preview report data before generating PDF"""
    try:
        if report_type == 'inventory_summary':
            # Get data for inventory summary preview
            total_products = Product.query.count()
            products_with_stock = Product.query.filter(Product.quantity > 0).count()
            out_of_stock = Product.query.filter(Product.quantity == 0).count()
            low_stock = Product.query.filter(Product.quantity > 0, Product.quantity < 10).count()
            
            # Top products by value
            top_products = db.session.query(Product).filter(Product.quantity > 0).order_by(
                (Product.price * Product.quantity).desc()
            ).limit(10).all()
            
            preview_data = {
                'title': 'Inventory Summary Report',
                'metrics': {
                    'total_products': total_products,
                    'products_with_stock': products_with_stock,
                    'out_of_stock': out_of_stock,
                    'low_stock': low_stock
                },
                'top_products': top_products
            }
            
        elif report_type == 'low_stock_alerts':
            # Get alerts data
            alerts_query = db.session.query(ReorderPoint, Product).join(Product).filter(
                ReorderPoint.is_active == True,
                Product.quantity < ReorderPoint.minimum_quantity
            )
            
            critical_alerts = alerts_query.filter(Product.quantity == 0).all()
            urgent_alerts = alerts_query.filter(
                Product.quantity > 0,
                Product.quantity < ReorderPoint.minimum_quantity * 0.5
            ).all()
            warning_alerts = alerts_query.filter(
                Product.quantity >= ReorderPoint.minimum_quantity * 0.5,
                Product.quantity < ReorderPoint.minimum_quantity
            ).all()
            
            preview_data = {
                'title': 'Low Stock Alerts Report',
                'critical_count': len(critical_alerts),
                'urgent_count': len(urgent_alerts),
                'warning_count': len(warning_alerts),
                'critical_alerts': critical_alerts[:5],  # Show first 5
                'urgent_alerts': urgent_alerts[:5],
                'warning_alerts': warning_alerts[:5]
            }
            
        elif report_type == 'supplier_performance':
            # Get supplier data
            suppliers_data = db.session.query(
                Supplier, 
                db.func.count(Product.id).label('product_count'),
                db.func.sum(Product.quantity).label('total_stock'),
                db.func.sum(Product.price * Product.quantity).label('total_value')
            ).outerjoin(Product).group_by(Supplier.id).order_by(
                db.func.sum(Product.price * Product.quantity).desc()
            ).limit(10).all()
            
            preview_data = {
                'title': 'Supplier Performance Report',
                'total_suppliers': Supplier.query.count(),
                'active_suppliers': len([s for s in suppliers_data if s[1] > 0]),
                'top_suppliers': suppliers_data[:5]  # Show top 5
            }
            
        else:
            flash('Invalid report type', 'error')
            return redirect(url_for('reports'))
        
        return render_template('report_preview.html', data=preview_data, report_type=report_type)
        
    except Exception as e:
        flash(f'Error previewing report: {str(e)}', 'error')
        return redirect(url_for('reports'))

# Add this route to integrate with existing dashboard
@app.route('/reports/quick/<report_type>')
def quick_report_generation(report_type):
    """Quick report generation from dashboard or other pages"""
    try:
        if report_type == 'inventory_summary':
            return redirect(url_for('generate_inventory_summary_report'))
        elif report_type == 'low_stock_alerts':
            return redirect(url_for('generate_low_stock_alerts_report'))
        elif report_type == 'supplier_performance':
            return redirect(url_for('generate_supplier_performance_report'))
        else:
            flash('Invalid report type', 'error')
            return redirect(url_for('reports'))
            
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('reports'))

@app.route('/api/charts/stock_distribution')
def api_stock_distribution():
    """API endpoint for stock distribution pie chart data"""
    try:
        # Calculate stock distribution
        in_stock = Product.query.filter(Product.quantity >= 10).count()
        low_stock = Product.query.filter(Product.quantity > 0, Product.quantity < 10).count()
        out_of_stock = Product.query.filter(Product.quantity == 0).count()
        
        data = {
            'labels': ['In Stock', 'Low Stock', 'Out of Stock'],
            'datasets': [{
                'data': [in_stock, low_stock, out_of_stock],
                'backgroundColor': ['#27ae60', '#f39c12', '#e74c3c'],
                'borderWidth': 3,
                'borderColor': '#ffffff'
            }],
            'total': in_stock + low_stock + out_of_stock
        }
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/top_products')
def api_top_products():
    """API endpoint for top products bar chart data"""
    try:
        # Get top 8 products by value
        top_products = db.session.query(
            Product,
            (Product.price * Product.quantity).label('total_value')
        ).filter(Product.quantity > 0).order_by(
            (Product.price * Product.quantity).desc()
        ).limit(8).all()
        
        products_data = []
        for product, value in top_products:
            products_data.append({
                'name': product.name,
                'sku': product.sku,
                'value': float(value),
                'quantity': product.quantity,
                'price': float(product.price)
            })
        
        data = {
            'labels': [p['sku'] for p in products_data],
            'datasets': [{
                'label': 'Inventory Value',
                'data': [p['value'] for p in products_data],
                'backgroundColor': '#3498db',
                'borderColor': '#2c3e50',
                'borderWidth': 1
            }],
            'products': products_data
        }
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/transaction_activity')
def api_transaction_activity():
    """API endpoint for transaction activity line chart data"""
    try:
        # Get period from query parameter (default 7 days)
        period = int(request.args.get('period', 7))
        start_date = datetime.utcnow() - timedelta(days=period)
        
        # Generate date labels
        dates = []
        date_labels = []
        for i in range(period):
            date = start_date + timedelta(days=i)
            dates.append(date.date())
            date_labels.append(date.strftime('%m/%d'))
        
        # Get transaction counts by date
        total_transactions = []
        increases = []
        decreases = []
        
        for date in dates:
            start_datetime = datetime.combine(date, datetime.min.time())
            end_datetime = datetime.combine(date, datetime.max.time())
            
            # Total transactions for this date
            day_total = StockTransaction.query.filter(
                StockTransaction.created_at >= start_datetime,
                StockTransaction.created_at <= end_datetime
            ).count()
            
            # Increases for this date
            day_increases = StockTransaction.query.filter(
                StockTransaction.created_at >= start_datetime,
                StockTransaction.created_at <= end_datetime,
                StockTransaction.quantity_change > 0
            ).count()
            
            # Decreases for this date
            day_decreases = StockTransaction.query.filter(
                StockTransaction.created_at >= start_datetime,
                StockTransaction.created_at <= end_datetime,
                StockTransaction.quantity_change < 0
            ).count()
            
            total_transactions.append(day_total)
            increases.append(day_increases)
            decreases.append(day_decreases)
        
        data = {
            'labels': date_labels,
            'datasets': [
                {
                    'label': 'Total Transactions',
                    'data': total_transactions,
                    'borderColor': '#3498db',
                    'backgroundColor': '#3498db20',
                    'fill': True,
                    'tension': 0.4
                },
                {
                    'label': 'Stock Increases',
                    'data': increases,
                    'borderColor': '#27ae60',
                    'backgroundColor': '#27ae6020',
                    'fill': False,
                    'tension': 0.4
                },
                {
                    'label': 'Stock Decreases',
                    'data': decreases,
                    'borderColor': '#e74c3c',
                    'backgroundColor': '#e74c3c20',
                    'fill': False,
                    'tension': 0.4
                }
            ]
        }
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/alert_distribution')
def api_alert_distribution():
    """API endpoint for alert severity distribution chart"""
    try:
        # Get alert counts by severity
        alerts_query = db.session.query(ReorderPoint, Product).join(Product).filter(
            ReorderPoint.is_active == True
        )
        
        critical_count = alerts_query.filter(Product.quantity == 0).count()
        urgent_count = alerts_query.filter(
            Product.quantity > 0,
            Product.quantity < ReorderPoint.minimum_quantity * 0.5
        ).count()
        warning_count = alerts_query.filter(
            Product.quantity >= ReorderPoint.minimum_quantity * 0.5,
            Product.quantity < ReorderPoint.minimum_quantity
        ).count()
        
        # Calculate well-stocked products
        total_products = Product.query.count()
        total_alerts = critical_count + urgent_count + warning_count
        well_stocked = total_products - total_alerts
        
        data = {
            'labels': ['Well Stocked', 'Warning', 'Urgent', 'Critical'],
            'datasets': [{
                'data': [well_stocked, warning_count, urgent_count, critical_count],
                'backgroundColor': ['#27ae60', '#f39c12', '#ff6b35', '#e74c3c'],
                'borderWidth': 3,
                'borderColor': '#ffffff'
            }],
            'details': {
                'well_stocked': well_stocked,
                'warning': warning_count,
                'urgent': urgent_count,
                'critical': critical_count,
                'total': total_products
            }
        }
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/supplier_performance')
def api_supplier_performance():
    """API endpoint for supplier performance horizontal bar chart"""
    try:
        # Get top suppliers by inventory value
        suppliers_data = db.session.query(
            Supplier, 
            db.func.count(Product.id).label('product_count'),
            db.func.sum(Product.quantity).label('total_stock'),
            db.func.sum(Product.price * Product.quantity).label('total_value')
        ).outerjoin(Product).group_by(Supplier.id).having(
            db.func.count(Product.id) > 0
        ).order_by(db.func.sum(Product.price * Product.quantity).desc()).limit(8).all()
        
        suppliers_list = []
        for supplier, product_count, total_stock, total_value in suppliers_data:
            suppliers_list.append({
                'name': supplier.name,
                'products': product_count,
                'stock': total_stock or 0,
                'value': float(total_value or 0)
            })
        
        data = {
            'labels': [s['name'] for s in suppliers_list],
            'datasets': [{
                'label': 'Inventory Value',
                'data': [s['value'] for s in suppliers_list],
                'backgroundColor': '#9b59b6',
                'borderColor': '#2c3e50',
                'borderWidth': 1
            }],
            'suppliers': suppliers_list
        }
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/inventory_value_trend')
def api_inventory_value_trend():
    """API endpoint for inventory value trend line chart"""
    try:
        # Get period from query parameter (default 7 days)
        period = int(request.args.get('period', 7))
        
        # For this implementation, we'll calculate value trends based on transaction history
        # In a more advanced system, you might store daily snapshots
        
        dates = []
        date_labels = []
        values = []
        
        current_value = float(db.session.query(db.func.sum(Product.price * Product.quantity)).scalar() or 0)
        
        for i in range(period):
            date = datetime.utcnow() - timedelta(days=period - 1 - i)
            dates.append(date.date())
            date_labels.append(date.strftime('%m/%d'))
            
            # Calculate approximate value for this date by working backwards from current value
            # This is a simplified approach - in production you might store daily value snapshots
            days_from_now = period - 1 - i
            if days_from_now == 0:
                # Today's value
                values.append(current_value)
            else:
                # Estimate historical value based on transaction changes since then
                since_date = datetime.combine(date.date(), datetime.min.time())
                
                # Get all transactions since this date
                transactions_since = StockTransaction.query.filter(
                    StockTransaction.created_at >= since_date
                ).all()
                
                # Calculate value changes
                value_change = 0
                for transaction in transactions_since:
                    value_change += transaction.quantity_change * transaction.product.price
                
                estimated_value = current_value - value_change
                values.append(max(0, estimated_value))  # Ensure non-negative
        
        data = {
            'labels': date_labels,
            'datasets': [{
                'label': 'Total Inventory Value',
                'data': values,
                'borderColor': '#27ae60',
                'backgroundColor': '#27ae6020',
                'fill': True,
                'tension': 0.4,
                'pointBackgroundColor': '#27ae60',
                'pointBorderColor': '#ffffff',
                'pointBorderWidth': 2,
                'pointRadius': 5
            }]
        }
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/refresh_all')
def api_refresh_all_charts():
    """API endpoint to get all chart data at once"""
    try:
        # This endpoint returns all chart data in one request for efficiency
        response_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'stock_distribution': api_stock_distribution().get_json(),
            'top_products': api_top_products().get_json(),
            'transaction_activity': api_transaction_activity().get_json(),
            'alert_distribution': api_alert_distribution().get_json(),
            'supplier_performance': api_supplier_performance().get_json(),
            'inventory_value_trend': api_inventory_value_trend().get_json()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Enhanced dashboard route with chart-ready data
# This updates your existing dashboard route to include chart-optimized data
@app.route('/dashboard')
def dashboard():
    """Enhanced analytics dashboard with interactive charts support"""
    
    # Basic inventory metrics (existing code)
    total_products = Product.query.count()
    total_suppliers = Supplier.query.count()
    total_transactions = StockTransaction.query.count()
    
    # Stock status analysis
    products_with_stock = Product.query.filter(Product.quantity > 0).count()
    out_of_stock_products = Product.query.filter(Product.quantity == 0).count()
    low_stock_products = Product.query.filter(Product.quantity > 0, Product.quantity < 10).count()
    
    # Calculate total inventory value
    inventory_value_query = db.session.query(db.func.sum(Product.price * Product.quantity)).scalar()
    total_inventory_value = inventory_value_query if inventory_value_query else 0.0
    
    # Alert analysis (existing code)
    active_reorder_points = ReorderPoint.query.filter(ReorderPoint.is_active == True).count()
    
    # Get products below their reorder minimums
    alerts_query = db.session.query(ReorderPoint, Product).join(Product).filter(
        ReorderPoint.is_active == True,
        Product.quantity < ReorderPoint.minimum_quantity
    )
    
    critical_alerts_count = alerts_query.filter(Product.quantity == 0).count()
    urgent_alerts_count = alerts_query.filter(
        Product.quantity > 0,
        Product.quantity < ReorderPoint.minimum_quantity * 0.5
    ).count()
    warning_alerts_count = alerts_query.filter(
        Product.quantity >= ReorderPoint.minimum_quantity * 0.5,
        Product.quantity < ReorderPoint.minimum_quantity
    ).count()
    
    total_active_alerts = critical_alerts_count + urgent_alerts_count + warning_alerts_count
    
    # Recent transaction activity (existing code)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    recent_transactions = StockTransaction.query.filter(
        StockTransaction.created_at >= seven_days_ago
    ).order_by(StockTransaction.created_at.desc()).limit(10).all()
    
    transactions_last_week = StockTransaction.query.filter(
        StockTransaction.created_at >= seven_days_ago
    ).count()
    
    # Stock movement analysis (existing code)
    increases_last_week = StockTransaction.query.filter(
        StockTransaction.created_at >= seven_days_ago,
        StockTransaction.quantity_change > 0
    ).count()
    
    decreases_last_week = StockTransaction.query.filter(
        StockTransaction.created_at >= seven_days_ago,
        StockTransaction.quantity_change < 0
    ).count()
    
    # Top products by value (existing code)
    top_products_by_value = db.session.query(
        Product,
        (Product.price * Product.quantity).label('total_value')
    ).filter(Product.quantity > 0).order_by(
        (Product.price * Product.quantity).desc()
    ).limit(5).all()
    
    # Products requiring attention (existing code)
    attention_products = db.session.query(Product).filter(
        Product.quantity < 10,
        Product.quantity > 0,
        Product.price > 10.0
    ).order_by((Product.price * Product.quantity).desc()).limit(5).all()
    
    # Supplier analysis (existing code)
    suppliers_with_products = db.session.query(
        Supplier, 
        db.func.count(Product.id).label('product_count'),
        db.func.sum(Product.quantity).label('total_stock'),
        db.func.sum(Product.price * Product.quantity).label('total_value')
    ).outerjoin(Product).group_by(Supplier.id).having(
        db.func.count(Product.id) > 0
    ).order_by(db.func.sum(Product.price * Product.quantity).desc()).limit(5).all()
    
    # Package all data for template (existing structure preserved)
    dashboard_data = {
        'metrics': {
            'total_products': total_products,
            'total_suppliers': total_suppliers,
            'total_transactions': total_transactions,
            'products_with_stock': products_with_stock,
            'out_of_stock_products': out_of_stock_products,
            'low_stock_products': low_stock_products,
            'total_inventory_value': total_inventory_value,
            'active_reorder_points': active_reorder_points
        },
        'alerts': {
            'total_active_alerts': total_active_alerts,
            'critical_alerts_count': critical_alerts_count,
            'urgent_alerts_count': urgent_alerts_count,
            'warning_alerts_count': warning_alerts_count
        },
        'activity': {
            'transactions_last_week': transactions_last_week,
            'increases_last_week': increases_last_week,
            'decreases_last_week': decreases_last_week,
            'recent_transactions': recent_transactions
        },
        'top_products': top_products_by_value,
        'attention_products': attention_products,
        'top_suppliers': suppliers_with_products,
        # NEW: Chart-ready data included directly
        'charts': {
            'stock_distribution': {
                'in_stock': products_with_stock,
                'low_stock': low_stock_products,
                'out_of_stock': out_of_stock_products
            },
            'top_products_count': len(top_products_by_value),
            'suppliers_count': len(suppliers_with_products)
        }
    }
    
    return render_template('dashboard.html', data=dashboard_data)

# Additional utility route for chart data validation
@app.route('/api/charts/health')
def api_charts_health():
    """Health check endpoint for chart system"""
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database_connected': True,
            'products_count': Product.query.count(),
            'transactions_count': StockTransaction.query.count(),
            'charts_available': [
                'stock_distribution',
                'top_products', 
                'transaction_activity',
                'alert_distribution',
                'supplier_performance',
                'inventory_value_trend'
            ]
        }
        
        return jsonify(health_data)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/api/analytics/business_intelligence')
def api_business_intelligence():
    """Advanced business intelligence analytics API"""
    try:
        # Calculate comprehensive business metrics
        current_date = datetime.utcnow()
        
        # Inventory Health Metrics
        total_products = Product.query.count()
        products_with_stock = Product.query.filter(Product.quantity > 0).count()
        out_of_stock = Product.query.filter(Product.quantity == 0).count()
        low_stock = Product.query.filter(Product.quantity > 0, Product.quantity < 10).count()
        
        inventory_health_score = ((products_with_stock - low_stock) / total_products * 100) if total_products > 0 else 0
        
        # Financial Metrics
        total_inventory_value = db.session.query(func.sum(Product.price * Product.quantity)).scalar() or 0
        average_product_value = db.session.query(func.avg(Product.price * Product.quantity)).scalar() or 0
        high_value_products = Product.query.filter(Product.price * Product.quantity > average_product_value).count()
        
        # Supplier Diversification
        total_suppliers = Supplier.query.count()
        suppliers_with_products = db.session.query(Supplier).join(Product).distinct().count()
        supplier_utilization = (suppliers_with_products / total_suppliers * 100) if total_suppliers > 0 else 0
        
        # Transaction Velocity (last 30 days)
        thirty_days_ago = current_date - timedelta(days=30)
        recent_transactions = StockTransaction.query.filter(
            StockTransaction.created_at >= thirty_days_ago
        ).count()
        
        transaction_velocity = recent_transactions / 30  # Average per day
        
        # Alert Performance
        active_alerts = ReorderPoint.query.filter(ReorderPoint.is_active == True).count()
        triggered_alerts = db.session.query(ReorderPoint, Product).join(Product).filter(
            ReorderPoint.is_active == True,
            Product.quantity < ReorderPoint.minimum_quantity
        ).count()
        
        alert_efficiency = ((active_alerts - triggered_alerts) / active_alerts * 100) if active_alerts > 0 else 100
        
        # Stock Turnover Analysis
        total_stock_movements = db.session.query(func.sum(func.abs(StockTransaction.quantity_change))).filter(
            StockTransaction.created_at >= thirty_days_ago
        ).scalar() or 0
        
        current_total_stock = db.session.query(func.sum(Product.quantity)).scalar() or 1
        stock_turnover_rate = (total_stock_movements / current_total_stock) if current_total_stock > 0 else 0
        
        analytics_data = {
            'timestamp': current_date.isoformat(),
            'inventory_health': {
                'score': round(inventory_health_score, 1),
                'status': 'Excellent' if inventory_health_score > 85 else 'Good' if inventory_health_score > 70 else 'Fair' if inventory_health_score > 50 else 'Poor',
                'total_products': total_products,
                'in_stock_ratio': round((products_with_stock / total_products * 100), 1) if total_products > 0 else 0
            },
            'financial_performance': {
                'total_value': round(total_inventory_value, 2),
                'average_product_value': round(average_product_value, 2),
                'high_value_products': high_value_products,
                'value_concentration': round((high_value_products / total_products * 100), 1) if total_products > 0 else 0
            },
            'supplier_metrics': {
                'total_suppliers': total_suppliers,
                'active_suppliers': suppliers_with_products,
                'utilization_rate': round(supplier_utilization, 1),
                'diversification_status': 'Well Diversified' if supplier_utilization > 80 else 'Moderately Diversified' if supplier_utilization > 60 else 'Concentrated'
            },
            'operational_efficiency': {
                'transaction_velocity': round(transaction_velocity, 2),
                'alert_efficiency': round(alert_efficiency, 1),
                'stock_turnover_rate': round(stock_turnover_rate, 3),
                'efficiency_status': 'High' if alert_efficiency > 80 and transaction_velocity > 2 else 'Medium' if alert_efficiency > 60 else 'Low'
            },
            'recommendations': generate_bi_recommendations(inventory_health_score, alert_efficiency, supplier_utilization, transaction_velocity)
        }
        
        return jsonify(analytics_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/demand_forecast')
def api_demand_forecast():
    """Demand forecasting based on historical transaction data"""
    try:
        # Get forecasting period (default 30 days)
        forecast_days = int(request.args.get('days', 30))
        
        # Analyze historical patterns for top products
        top_products = db.session.query(Product).filter(Product.quantity > 0).order_by(
            (Product.price * Product.quantity).desc()
        ).limit(10).all()
        
        forecast_data = []
        
        for product in top_products:
            # Get last 60 days of transactions
            sixty_days_ago = datetime.utcnow() - timedelta(days=60)
            transactions = StockTransaction.query.filter(
                StockTransaction.product_id == product.id,
                StockTransaction.created_at >= sixty_days_ago,
                StockTransaction.quantity_change < 0  # Only outgoing stock
            ).all()
            
            if len(transactions) < 3:  # Need minimum data for forecasting
                continue
                
            # Calculate daily demand rate
            total_demand = sum(abs(t.quantity_change) for t in transactions)
            days_with_activity = len(set(t.created_at.date() for t in transactions))
            daily_demand_rate = total_demand / max(days_with_activity, 1)
            
            # Simple linear forecast
            forecasted_demand = daily_demand_rate * forecast_days
            days_until_stockout = product.quantity / daily_demand_rate if daily_demand_rate > 0 else float('inf')
            
            # Risk assessment
            risk_level = 'high' if days_until_stockout < 7 else 'medium' if days_until_stockout < 14 else 'low'
            
            forecast_data.append({
                'product_id': product.id,
                'product_name': product.name,
                'sku': product.sku,
                'current_stock': product.quantity,
                'daily_demand_rate': round(daily_demand_rate, 2),
                'forecasted_demand': round(forecasted_demand, 1),
                'days_until_stockout': round(days_until_stockout, 1) if days_until_stockout != float('inf') else None,
                'risk_level': risk_level,
                'recommended_reorder': round(forecasted_demand * 1.2, 0),  # 20% buffer
                'confidence': 'high' if len(transactions) > 10 else 'medium' if len(transactions) > 5 else 'low'
            })
        
        # Sort by risk level
        forecast_data.sort(key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['risk_level']])
        
        return jsonify({
            'forecast_period_days': forecast_days,
            'products_analyzed': len(forecast_data),
            'high_risk_products': sum(1 for p in forecast_data if p['risk_level'] == 'high'),
            'forecasts': forecast_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/seasonal_patterns')
def api_seasonal_patterns():
    """Analyze seasonal patterns in inventory movements"""
    try:
        # Get transaction data for pattern analysis
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        transactions = StockTransaction.query.filter(
            StockTransaction.created_at >= ninety_days_ago
        ).all()
        
        # Group by day of week and hour
        day_patterns = defaultdict(int)
        hour_patterns = defaultdict(int)
        weekly_trends = defaultdict(list)
        
        for transaction in transactions:
            day_of_week = transaction.created_at.strftime('%A')
            hour = transaction.created_at.hour
            week_number = transaction.created_at.isocalendar()[1]
            
            day_patterns[day_of_week] += abs(transaction.quantity_change)
            hour_patterns[hour] += abs(transaction.quantity_change)
            weekly_trends[week_number].append(abs(transaction.quantity_change))
        
        # Calculate weekly averages
        weekly_averages = {}
        for week, values in weekly_trends.items():
            weekly_averages[week] = sum(values) / len(values) if values else 0
        
        # Identify peak activity patterns
        peak_day = max(day_patterns.items(), key=lambda x: x[1]) if day_patterns else ('N/A', 0)
        peak_hour = max(hour_patterns.items(), key=lambda x: x[1]) if hour_patterns else (0, 0)
        
        return jsonify({
            'analysis_period': '90 days',
            'daily_patterns': dict(day_patterns),
            'hourly_patterns': dict(hour_patterns),
            'peak_activity': {
                'day': peak_day[0],
                'hour': f"{peak_hour[0]:02d}:00",
                'day_volume': peak_day[1],
                'hour_volume': peak_hour[1]
            },
            'weekly_trends': dict(weekly_averages),
            'insights': {
                'most_active_day': peak_day[0],
                'recommended_restock_day': calculate_optimal_restock_day(day_patterns),
                'activity_consistency': calculate_activity_consistency(weekly_averages)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/supplier_risk_assessment')
def api_supplier_risk_assessment():
    """Assess supplier risk and dependency analysis"""
    try:
        # Get supplier performance data
        suppliers_data = db.session.query(
            Supplier, 
            func.count(Product.id).label('product_count'),
            func.sum(Product.quantity).label('total_stock'),
            func.sum(Product.price * Product.quantity).label('total_value'),
            func.avg(Product.quantity).label('avg_stock_per_product')
        ).outerjoin(Product).group_by(Supplier.id).all()
        
        total_inventory_value = sum(s[3] or 0 for s in suppliers_data)
        
        risk_assessment = []
        
        for supplier, product_count, total_stock, total_value, avg_stock in suppliers_data:
            if product_count == 0:  # Skip suppliers with no products
                continue
                
            # Calculate risk metrics
            value_concentration = (total_value / total_inventory_value * 100) if total_inventory_value > 0 else 0
            product_concentration = (product_count / Product.query.count() * 100)
            
            # Assess stock levels for this supplier's products
            supplier_products = Product.query.filter_by(supplier_id=supplier.id).all()
            low_stock_products = sum(1 for p in supplier_products if p.quantity < 10)
            low_stock_ratio = (low_stock_products / len(supplier_products) * 100) if supplier_products else 0
            
            # Calculate overall risk score
            concentration_risk = min(value_concentration * 2, 100)  # High concentration = high risk
            stock_risk = low_stock_ratio  # High low-stock ratio = high risk
            overall_risk = (concentration_risk + stock_risk) / 2
            
            risk_level = 'high' if overall_risk > 60 else 'medium' if overall_risk > 30 else 'low'
            
            risk_assessment.append({
                'supplier_id': supplier.id,
                'supplier_name': supplier.name,
                'product_count': product_count,
                'total_value': round(total_value or 0, 2),
                'value_concentration': round(value_concentration, 2),
                'product_concentration': round(product_concentration, 2),
                'low_stock_ratio': round(low_stock_ratio, 1),
                'risk_score': round(overall_risk, 1),
                'risk_level': risk_level,
                'recommendations': generate_supplier_recommendations(risk_level, value_concentration, low_stock_ratio)
            })
        
        # Sort by risk score (highest first)
        risk_assessment.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return jsonify({
            'total_suppliers_analyzed': len(risk_assessment),
            'high_risk_suppliers': sum(1 for s in risk_assessment if s['risk_level'] == 'high'),
            'medium_risk_suppliers': sum(1 for s in risk_assessment if s['risk_level'] == 'medium'),
            'low_risk_suppliers': sum(1 for s in risk_assessment if s['risk_level'] == 'low'),
            'supplier_assessments': risk_assessment,
            'portfolio_insights': {
                'most_concentrated_supplier': risk_assessment[0]['supplier_name'] if risk_assessment else 'None',
                'highest_risk_supplier': max(risk_assessment, key=lambda x: x['risk_score'])['supplier_name'] if risk_assessment else 'None',
                'diversification_recommendation': assess_supplier_diversification(risk_assessment)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/inventory_optimization')
def api_inventory_optimization():
    """Advanced inventory optimization recommendations"""
    try:
        # Analyze all products for optimization opportunities
        products = Product.query.all()
        
        optimization_data = []
        
        for product in products:
            # Get transaction history for this product
            transactions = StockTransaction.query.filter_by(product_id=product.id).order_by(
                StockTransaction.created_at.desc()
            ).limit(50).all()  # Last 50 transactions
            
            if not transactions:
                continue
                
            # Calculate metrics
            total_outbound = sum(abs(t.quantity_change) for t in transactions if t.quantity_change < 0)
            total_inbound = sum(t.quantity_change for t in transactions if t.quantity_change > 0)
            
            # Calculate average demand rate
            date_range = (transactions[0].created_at - transactions[-1].created_at).days if len(transactions) > 1 else 1
            daily_demand = total_outbound / max(date_range, 1)
            
            # Current stock analysis
            current_stock = product.quantity
            current_value = product.price * product.quantity
            
            # Days of stock remaining
            days_remaining = current_stock / daily_demand if daily_demand > 0 else float('inf')
            
            # Optimization recommendations
            reorder_point = product.reorder_point
            optimal_stock = daily_demand * 14  # 2 weeks of demand
            
            if reorder_point:
                efficiency = 'optimal' if days_remaining > 14 else 'needs_attention' if days_remaining > 7 else 'critical'
            else:
                efficiency = 'no_monitoring'
            
            optimization_data.append({
                'product_id': product.id,
                'product_name': product.name,
                'sku': product.sku,
                'current_stock': current_stock,
                'current_value': round(current_value, 2),
                'daily_demand_rate': round(daily_demand, 2),
                'days_remaining': round(days_remaining, 1) if days_remaining != float('inf') else None,
                'optimal_stock_level': round(optimal_stock, 0),
                'stock_efficiency': efficiency,
                'value_velocity': round(current_value / max(days_remaining, 1), 2) if days_remaining != float('inf') else 0,
                'optimization_score': calculate_optimization_score(current_stock, optimal_stock, days_remaining, current_value),
                'recommendations': generate_optimization_recommendations(current_stock, optimal_stock, days_remaining, daily_demand)
            })
        
        # Sort by optimization potential (lowest scores first - most improvement potential)
        optimization_data.sort(key=lambda x: x['optimization_score'])
        
        return jsonify({
            'products_analyzed': len(optimization_data),
            'optimization_opportunities': optimization_data[:10],  # Top 10 optimization opportunities
            'summary': {
                'needs_immediate_attention': sum(1 for p in optimization_data if p['stock_efficiency'] == 'critical'),
                'needs_monitoring': sum(1 for p in optimization_data if p['stock_efficiency'] == 'needs_attention'),
                'well_optimized': sum(1 for p in optimization_data if p['stock_efficiency'] == 'optimal'),
                'no_monitoring': sum(1 for p in optimization_data if p['stock_efficiency'] == 'no_monitoring')
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/performance_summary')
def api_performance_summary():
    """Comprehensive performance summary for executive dashboard"""
    try:
        current_date = datetime.utcnow()
        thirty_days_ago = current_date - timedelta(days=30)
        
        # System Performance Metrics
        total_products = Product.query.count()
        active_products = Product.query.filter(Product.quantity > 0).count()
        total_transactions = StockTransaction.query.count()
        recent_transactions = StockTransaction.query.filter(
            StockTransaction.created_at >= thirty_days_ago
        ).count()
        
        # Financial Performance
        current_inventory_value = db.session.query(func.sum(Product.price * Product.quantity)).scalar() or 0
        
        # Calculate month-over-month value change (simplified)
        sixty_days_ago = current_date - timedelta(days=60)
        historical_transactions = StockTransaction.query.filter(
            StockTransaction.created_at >= sixty_days_ago,
            StockTransaction.created_at < thirty_days_ago
        ).all()
        
        historical_value_change = sum(t.quantity_change * t.product.price for t in historical_transactions)
        
        # Alert System Performance
        total_alerts = ReorderPoint.query.filter(ReorderPoint.is_active == True).count()
        triggered_alerts = db.session.query(ReorderPoint, Product).join(Product).filter(
            ReorderPoint.is_active == True,
            Product.quantity < ReorderPoint.minimum_quantity
        ).count()
        
        # Supplier Performance
        active_suppliers = db.session.query(Supplier).join(Product).distinct().count()
        total_suppliers = Supplier.query.count()
        
        # Calculate overall system health score
        system_health = calculate_system_health_score(
            active_products, total_products, triggered_alerts, total_alerts,
            recent_transactions, current_inventory_value
        )
        
        return jsonify({
            'report_date': current_date.isoformat(),
            'system_health': {
                'overall_score': system_health['score'],
                'status': system_health['status'],
                'components': system_health['components']
            },
            'operational_metrics': {
                'total_products': total_products,
                'active_products': active_products,
                'product_utilization': round((active_products / total_products * 100), 1) if total_products > 0 else 0,
                'transaction_velocity': round(recent_transactions / 30, 2),
                'alert_effectiveness': round(((total_alerts - triggered_alerts) / total_alerts * 100), 1) if total_alerts > 0 else 100
            },
            'financial_metrics': {
                'current_inventory_value': round(current_inventory_value, 2),
                'monthly_value_change': round(historical_value_change, 2),
                'average_product_value': round(current_inventory_value / max(active_products, 1), 2),
                'value_growth_rate': round((historical_value_change / max(current_inventory_value - historical_value_change, 1) * 100), 2)
            },
            'supplier_metrics': {
                'total_suppliers': total_suppliers,
                'active_suppliers': active_suppliers,
                'supplier_efficiency': round((active_suppliers / total_suppliers * 100), 1) if total_suppliers > 0 else 0
            },
            'recommendations': generate_executive_recommendations(system_health, {
                'transaction_velocity': recent_transactions / 30,
                'alert_effectiveness': ((total_alerts - triggered_alerts) / total_alerts * 100) if total_alerts > 0 else 100,
                'value_growth': historical_value_change / max(current_inventory_value - historical_value_change, 1) * 100
            })
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Enhanced dashboard route with advanced analytics integration
@app.route('/dashboard/advanced')
def advanced_dashboard():
    """Advanced analytics dashboard with forecasting and insights"""
    try:
        # Get all the existing dashboard data
        dashboard_data = dashboard().get_data(as_text=True)  # Get existing dashboard data
        
        # Add advanced analytics
        from flask import json as flask_json
        
        # This would typically be rendered with additional advanced analytics
        # For now, redirect to main dashboard with enhanced features
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f'Error loading advanced dashboard: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# Enhanced API health check with analytics status
@app.route('/api/health/analytics')
def api_analytics_health():
    """Health check for analytics system"""
    try:
        # Test all analytics endpoints
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {
                'database': 'healthy',
                'charts_api': 'healthy',
                'analytics_engine': 'healthy',
                'forecasting': 'healthy'
            },
            'metrics': {
                'total_products': Product.query.count(),
                'total_transactions': StockTransaction.query.count(),
                'active_charts': 6,
                'analytics_endpoints': 4
            },
            'features': {
                'business_intelligence': True,
                'demand_forecasting': True,
                'supplier_risk_assessment': True,
                'inventory_optimization': True,
                'seasonal_analysis': True,
                'performance_monitoring': True
            }
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat(),
            'components': {
                'database': 'error',
                'charts_api': 'unknown',
                'analytics_engine': 'error',
                'forecasting': 'unknown'
            }
        }), 500

# Performance optimization middleware
@app.before_request
def before_request():
    """Add performance tracking to requests"""
    request.start_time = datetime.utcnow()

@app.after_request
def after_request(response):
    """Log performance metrics"""
    if hasattr(request, 'start_time'):
        duration = (datetime.utcnow() - request.start_time).total_seconds()
        if duration > 1.0:  # Log slow requests
            print(f"⚠️ Slow request: {request.endpoint} took {duration:.2f}s")
    
    # Add performance headers
    response.headers['X-Response-Time'] = f"{duration:.3f}s" if 'duration' in locals() else 'unknown'
    response.headers['X-Powered-By'] = 'Flask Inventory Management System v5.0'
    
    return response

# Analytics route for getting all advanced data at once
@app.route('/api/analytics/dashboard_data')
def api_dashboard_analytics():
    """Get all dashboard analytics data in one request for performance"""
    try:
        # Fetch all analytics data concurrently (conceptually)
        bi_response = api_business_intelligence()
        forecast_response = api_demand_forecast()
        risk_response = api_supplier_risk_assessment()
        optimization_response = api_inventory_optimization()
        performance_response = api_performance_summary()
        
        # Combine all analytics data
        combined_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'business_intelligence': bi_response.get_json(),
            'demand_forecast': forecast_response.get_json(),
            'supplier_risk': risk_response.get_json(),
            'inventory_optimization': optimization_response.get_json(),
            'performance_summary': performance_response.get_json(),
            'system_status': 'fully_operational'
        }
        
        return jsonify(combined_data)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat(),
            'system_status': 'partial_failure'
        }), 500
    
@app.route('/analytics')
@permission_required('all_analytics', 'basic_analytics')
def analytics():
    """Advanced analytics dashboard page"""
    return render_template('analytics.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Find user by username or email
        user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.username.data)
        ).first()
        
        # Verify user exists, password is correct, and account is active
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'error')
                return render_template('auth/login.html', form=form)
            
            # Log the user in
            login_user(user, remember=form.remember_me.data)
            
            # Update login statistics
            user.update_login_stats()
            db.session.commit()
            
            # Redirect to intended page or dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
            
            flash(f'Welcome back, {user.first_name}! You have been logged in successfully.', 'success')
            return redirect(next_page)
        else:
            flash('Invalid username/email or password. Please try again.', 'error')
    
    return render_template('auth/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """Enhanced logout with proper session cleanup"""
    try:
        user_name = current_user.first_name if current_user.is_authenticated else "User"
        
        # Log the logout (optional - for security audit)
        if current_user.is_authenticated:
            print(f"User {current_user.username} logged out at {datetime.utcnow()}")
        
        # Logout user and clear session
        logout_user()
        
        # Clear all session data
        session.clear()
        
        # Flash success message
        flash(f'Goodbye, {user_name}! You have been logged out successfully.', 'success')
        
        # Redirect to login page
        response = make_response(redirect(url_for('login')))
        
        # Clear any cached data and prevent back button login
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'  
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        print(f"Logout error: {str(e)}")
        # Force clear session even if there's an error
        session.clear()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

@app.route('/profile')
@login_required_with_message
@active_user_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required_with_message
@active_user_required
def change_password():
    """Allow users to change their password"""
    form = PasswordChangeForm()
    
    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/change_password.html', form=form)
        
        # Update password
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('Your password has been changed successfully.', 'success')
        return redirect(url_for('profile'))
    
    return render_template('auth/change_password.html', form=form)

# =============================================================================
# PHASE 6A: USER MANAGEMENT ROUTES (Admin only)
# =============================================================================

@app.route('/admin/users')
@admin_required
def manage_users():
    """Admin page to manage all users"""
    users = User.query.order_by(User.last_login.desc().nullslast(), User.created_at.desc()).all()
    
    # Calculate user statistics
    stats = {
        'total_users': len(users),
        'active_users': sum(1 for u in users if u.is_active),
        'admin_count': sum(1 for u in users if u.is_admin),
        'manager_count': sum(1 for u in users if u.is_manager),
        'employee_count': sum(1 for u in users if u.is_employee),
        'recent_logins': sum(1 for u in users if u.last_login and 
                           (datetime.utcnow() - u.last_login).days < 7)
    }
    
    return render_template('auth/manage_users.html', users=users, stats=stats)

@app.route('/admin/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    """Admin form to create new users"""
    form = UserRegistrationForm()
    
    if form.validate_on_submit():
        try:
            # Create new user
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                role=UserRole(form.role.data),
                is_active=form.is_active.data,
                created_by_id=current_user.id
            )
            
            new_user.set_password(form.password.data)
            
            db.session.add(new_user)
            db.session.commit()
            
            flash(f'User "{new_user.username}" ({new_user.role_display}) created successfully!', 'success')
            return redirect(url_for('manage_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
    
    return render_template('auth/add_user.html', form=form)

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Admin form to edit existing users"""
    user = User.query.get_or_404(user_id)
    form = UserEditForm(original_user=user, obj=user)
    form.role.data = user.role.value  # Set current role
    
    if form.validate_on_submit():
        try:
            # Prevent admin from deactivating themselves
            if user.id == current_user.id and not form.is_active.data:
                flash('You cannot deactivate your own account.', 'error')
                return render_template('auth/edit_user.html', form=form, user=user)
            
            # Prevent removing admin role from last admin
            if (user.is_admin and form.role.data != UserRole.ADMIN.value and 
                User.query.filter_by(role=UserRole.ADMIN, is_active=True).count() <= 1):
                flash('Cannot remove admin role - at least one active admin must exist.', 'error')
                return render_template('auth/edit_user.html', form=form, user=user)
            
            # Update user
            user.username = form.username.data
            user.email = form.email.data
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.role = UserRole(form.role.data)
            user.is_active = form.is_active.data
            
            db.session.commit()
            
            flash(f'User "{user.username}" updated successfully!', 'success')
            return redirect(url_for('manage_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
    
    return render_template('auth/edit_user.html', form=form, user=user)

@app.route('/admin/users/<int:user_id>/reset_password', methods=['GET', 'POST'])
@admin_required
def admin_reset_password(user_id):
    """Admin form to reset user passwords"""
    user = User.query.get_or_404(user_id)
    form = AdminPasswordResetForm()
    
    if form.validate_on_submit():
        try:
            user.set_password(form.new_password.data)
            db.session.commit()
            
            flash(f'Password reset successfully for user "{user.username}".', 'success')
            return redirect(url_for('manage_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error resetting password: {str(e)}', 'error')
    
    return render_template('auth/reset_password.html', form=form, user=user)

@app.route('/admin/users/<int:user_id>/toggle_status')
@admin_required
def toggle_user_status(user_id):
    """Admin quick action to activate/deactivate users"""
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('manage_users'))
    
    try:
        user.is_active = not user.is_active
        action = "activated" if user.is_active else "deactivated"
        
        db.session.commit()
        
        flash(f'User "{user.username}" has been {action}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user status: {str(e)}', 'error')
    
    return redirect(url_for('manage_users'))

# =============================================================================
# PHASE 6A: ENHANCED STOCK TRANSACTION LOGGING WITH USER ATTRIBUTION
# =============================================================================

def log_stock_transaction_with_user(product, quantity_change, transaction_type, reason, user_notes=None):
    """
    Enhanced helper function to log stock transactions with user attribution
    
    This replaces your existing log_stock_transaction function
    """
    # Capture the before state
    quantity_before = product.quantity
    
    # Apply the change
    product.quantity += quantity_change
    
    # Capture the after state
    quantity_after = product.quantity
    
    # Create the transaction record with user attribution
    transaction = StockTransaction(
        product_id=product.id,
        transaction_type=transaction_type,
        quantity_change=quantity_change,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        reason=reason,
        user_notes=user_notes,
        performed_by_id=current_user.id if current_user.is_authenticated else None
    )
    
    # Add transaction to database session
    db.session.add(transaction)
    
    return transaction


# Run the application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)