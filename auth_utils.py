from functools import wraps
from flask import flash, redirect, url_for, request, abort, current_app
from flask_login import current_user
from models import UserRole

def login_required_with_message(f):
    """
    Enhanced login_required decorator with user-friendly messaging
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*required_roles):
    """
    Role-based access control decorator
    
    Usage:
    @role_required('admin')
    @role_required('admin', 'manager')
    @role_required(UserRole.ADMIN, UserRole.MANAGER)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'info')
                return redirect(url_for('login', next=request.url))
            
            # Convert string roles to UserRole enums
            roles_to_check = []
            for role in required_roles:
                if isinstance(role, str):
                    try:
                        roles_to_check.append(UserRole(role))
                    except ValueError:
                        current_app.logger.warning(f"Invalid role string: {role}")
                        continue
                elif isinstance(role, UserRole):
                    roles_to_check.append(role)
            
            # Check if user has any of the required roles
            if not any(current_user.has_role(role) for role in roles_to_check):
                role_names = [role.value.title() for role in roles_to_check]
                flash(f'Access denied. This page requires {" or ".join(role_names)} privileges.', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(*required_permissions):
    """
    Permission-based access control decorator
    
    Usage:
    @permission_required('user_management')
    @permission_required('all_analytics', 'all_reports')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'info')
                return redirect(url_for('login', next=request.url))
            
            # Check if user has any of the required permissions
            if not any(current_user.has_permission(perm) for perm in required_permissions):
                flash('Access denied. You do not have permission to access this page.', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    Shorthand decorator for admin-only access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('login', next=request.url))
        
        if not current_user.is_admin:
            flash('Access denied. This page requires Administrator privileges.', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def manager_or_admin_required(f):
    """
    Shorthand decorator for manager or admin access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('login', next=request.url))
        
        if not (current_user.is_admin or current_user.is_manager):
            flash('Access denied. This page requires Manager or Administrator privileges.', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def active_user_required(f):
    """
    Ensure user account is active
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('login', next=request.url))
        
        if not current_user.is_active:
            flash('Your account has been deactivated. Please contact an administrator.', 'error')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def self_or_admin_required(f):
    """
    Allow access to own profile or admin access to any profile
    
    Expected route parameter: user_id
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('login', next=request.url))
        
        user_id = kwargs.get('user_id') or kwargs.get('id')
        
        if user_id is None:
            abort(400)  # Bad request if no user_id provided
        
        # Allow if accessing own profile or user is admin
        if current_user.id == int(user_id) or current_user.is_admin:
            return f(*args, **kwargs)
        
        flash('Access denied. You can only access your own profile.', 'error')
        return redirect(url_for('dashboard'))
    
    return decorated_function

# Utility functions for templates and views
def get_user_permissions(user):
    """Get list of all permissions for a user (for debugging/admin)"""
    if not user or not user.is_authenticated:
        return set()
    
    all_permissions = {
        'user_management', 'system_config', 'all_analytics', 
        'all_reports', 'bulk_operations', 'import_export',
        'product_management', 'supplier_management', 'stock_operations',
        'alert_management', 'basic_analytics', 'product_view', 'basic_reports'
    }
    
    return {perm for perm in all_permissions if user.has_permission(perm)}

def check_feature_access(feature_name):
    """Check if current user has access to a specific feature"""
    if not current_user.is_authenticated:
        return False
    
    feature_permissions = {
        'analytics': ['all_analytics', 'basic_analytics'],
        'reports': ['all_reports', 'basic_reports'],
        'user_management': ['user_management'],
        'bulk_operations': ['bulk_operations'],
        'import_export': ['import_export'],
        'supplier_management': ['supplier_management'],
        'product_management': ['product_management'],
        'stock_operations': ['stock_operations'],
        'alert_management': ['alert_management']
    }
    
    required_perms = feature_permissions.get(feature_name, [])
    return any(current_user.has_permission(perm) for perm in required_perms)

# Context processor to make auth functions available in templates
def auth_template_context():
    """Add authentication context to all templates"""
    return {
        'current_user': current_user,
        'check_feature_access': check_feature_access,
        'UserRole': UserRole
    }