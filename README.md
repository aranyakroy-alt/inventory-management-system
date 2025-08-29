# Professional Inventory Management System

A comprehensive Flask-based inventory management system built with a systematic, phase-by-phase approach. Features advanced product management, supplier relationships, transaction logging, analytics dashboard, and automated alerts.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v2.0+-green.svg)
![SQLite](https://img.shields.io/badge/sqlite-v3+-orange.svg)
![Status](https://img.shields.io/badge/status-Phase%204%20Complete-success.svg)

## Features Overview

### Phase 1: Foundation (Complete ✅)
- Professional Flask web application
- SQLite database with SQLAlchemy ORM
- Responsive, modern UI design
- Basic product CRUD operations
- Stock level tracking with visual indicators

### Phase 2: Advanced Operations (Complete ✅)
- **Advanced Search**: Multi-field search across name, SKU, and description
- **Smart Filtering**: Filter by stock status (All/In Stock/Low Stock/Out of Stock)
- **Quick Stock Adjustments**: +/- buttons for instant inventory updates
- **Product Management**: Full edit/delete functionality with confirmations
- **Professional UI**: Mobile-responsive design with modern styling

### Phase 3: Supplier Management (Complete ✅)
- **Supplier Database**: Complete supplier information management
- **Supplier CRUD**: Add, edit, delete, and view suppliers with contact details
- **Product-Supplier Relationships**: Link products to suppliers with dropdown selection
- **Integrated Management**: Supplier information displayed in product listings
- **Safety Features**: Prevent deletion of suppliers with assigned products
- **Contact Management**: Store supplier contact person, email, phone, and address

### Phase 4: Smart Inventory Features (Complete ✅)

#### 4A: Transaction Logging System
- **Complete Audit Trail**: All stock movements tracked with before/after states
- **Transaction Types**: Manual adjustments, sales, purchases, returns, corrections
- **Automatic Logging**: Stock changes create transaction records automatically
- **Transaction History**: Filterable views with product-specific analytics
- **User Context**: Detailed reasons and notes for all changes

#### 4B: Low Stock Alert System
- **Configurable Reorder Points**: Set minimum thresholds per product
- **Intelligent Alerts**: Critical/urgent/warning severity levels
- **Automated Monitoring**: Real-time stock level assessment
- **Reorder Suggestions**: Calculated order quantities with supplier info
- **Alert Dashboard**: Centralized view of all products needing attention

#### 4C: Analytics Dashboard
- **Key Performance Indicators**: Inventory value, stock status, alert summaries
- **Top Products Analysis**: Highest value products and attention priorities
- **Supplier Performance**: Analytics ranked by inventory value and relationship
- **Recent Activity Feed**: Transaction history with visual indicators
- **Stock Health Overview**: Distribution and percentage breakdowns
- **Quick Action Hub**: Navigation shortcuts to major functions

#### 4D: Import/Export & Bulk Operations
- **CSV Export System**: Products, transactions, and alerts data export
- **Products Import**: SKU-based create/update logic with supplier auto-creation
- **Stock Adjustments Import**: Bulk quantity updates with transaction logging
- **CSV Templates**: Pre-formatted templates with current inventory data
- **Bulk Operations Interface**: Multi-product updates with change preview
- **Drag-and-Drop Upload**: Professional file handling with progress reporting
- **Comprehensive Validation**: Error handling, progress tracking, and data integrity

## Technology Stack

- **Backend**: Python Flask 2.0+, SQLAlchemy ORM
- **Database**: SQLite (development), easily upgradeable to PostgreSQL/MySQL
- **Frontend**: HTML5, CSS3, JavaScript (ES6)
- **Styling**: Custom responsive CSS with modern design patterns (~800+ lines)
- **Data Processing**: CSV import/export, transaction logging, bulk operations
- **Version Control**: Git with systematic commit history

## Installation & Setup

```bash
# Clone the repository
git clone https://github.com/aranyakroy-alt/inventory-management-system.git
cd inventory-management-system

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install flask flask-sqlalchemy

# Run the application
python app.py

# Open in browser
# http://localhost:5000
```

## Usage Guide

### Product Management
- **Add Products**: Professional forms with validation and supplier selection
- **Search & Filter**: Real-time search across multiple fields with smart filtering
- **Stock Adjustments**: Quick +/- controls and bulk adjustment tools
- **Edit/Delete**: Full CRUD operations with transaction logging
- **Product History**: Individual product transaction analytics and timeline

### Supplier Management
- **Supplier Database**: Complete contact and relationship management
- **Product Relationships**: Link products to suppliers with integrated views
- **Contact Management**: Store and manage supplier contact information
- **Safety Controls**: Protected deletion prevents data integrity issues

### Transaction & Analytics
- **Transaction History**: Complete audit trail with filtering and search
- **Analytics Dashboard**: Real-time KPIs, trends, and business insights
- **Low Stock Alerts**: Automated monitoring with configurable thresholds
- **Reorder Management**: Intelligent suggestions with supplier integration

### Data Management
- **Import/Export**: CSV-based data exchange with external systems
- **Bulk Operations**: Multi-product updates with transaction logging
- **Data Templates**: Pre-formatted CSV templates for easy import
- **Backup & Recovery**: Export capabilities for data backup

## Database Schema

```sql
Product:
- id (Primary Key)
- name (String, Required)
- sku (String, Unique, Required)  
- description (Text, Optional)
- price (Float, Required)
- quantity (Integer, Default: 0)
- supplier_id (Foreign Key to Supplier, Optional)
- created_at (DateTime, Auto-generated)

Supplier:
- id (Primary Key)
- name (String, Required)
- contact_person (String, Optional)
- email (String, Optional)
- phone (String, Optional)
- address (Text, Optional)
- created_at (DateTime, Auto-generated)

StockTransaction:
- id (Primary Key)
- product_id (Foreign Key to Product, Required)
- transaction_type (String, Required)
- quantity_change (Integer, Required)
- quantity_before (Integer, Required)
- quantity_after (Integer, Required)
- reason (String, Optional)
- user_notes (Text, Optional)
- created_at (DateTime, Auto-generated)

ReorderPoint:
- id (Primary Key)  
- product_id (Foreign Key to Product, Required, Unique)
- minimum_quantity (Integer, Required)
- reorder_quantity (Integer, Required)
- is_active (Boolean, Default: True)
- created_at (DateTime, Auto-generated)
- updated_at (DateTime, Auto-updated)
```

## Project Structure

```
inventory_system/
├── app.py                          # Main Flask application (18 routes)
├── models.py                       # Database models (4 models with relationships)
├── requirements.txt                # Project dependencies
├── README.md                      # Project documentation
├── .gitignore                     # Git ignore configuration
├── phase4_migration.py            # Transaction logging migration script
├── add_reorder_points.py          # Reorder points migration script
├── check_data.py                  # Database verification utility
├── fixed_migration.py             # Phase 3 supplier migration script
├── migration_database.py          # Database migration utilities
├── verify_migration.py            # Migration verification script
├── templates/                     # HTML templates with Jinja2 (17 files)
│   ├── base.html                  # Master template with navigation
│   ├── index.html                 # Homepage with dashboard preview
│   ├── dashboard.html             # Analytics dashboard (Phase 4C)
│   ├── products.html              # Product listing with search/filter/bulk operations
│   ├── add_product.html           # Product creation form with supplier integration
│   ├── edit_product.html          # Product editing with supplier selection
│   ├── suppliers.html             # Supplier management listing
│   ├── add_supplier.html          # Supplier creation form
│   ├── edit_supplier.html         # Supplier editing form
│   ├── transactions.html          # Transaction history with filtering (Phase 4A)
│   ├── product_history.html       # Individual product transaction analytics
│   ├── alerts.html                # Low stock alerts dashboard (Phase 4B)
│   ├── reorder_points.html        # Reorder point management interface
│   ├── manage_reorder_point.html  # Individual reorder point configuration
│   ├── import_export.html         # Import/export management page (Phase 4D)
│   ├── bulk_operations.html       # Bulk stock operations interface
│   ├── import_products.html       # Products import interface
│   └── import_stock_adjustments.html # Stock adjustments import interface
├── static/                        # CSS and assets
│   └── style.css                  # Professional responsive styling (~800+ lines)
├── venv/                          # Python virtual environment
├── instance/                      # SQLite database storage
│   └── inventory.db              # Main database file
└── .git/                         # Git repository
```

## Development Phases

### Completed Phases
- ✅ **Phase 1**: Foundation setup and basic functionality
- ✅ **Phase 2**: Advanced inventory operations and UI enhancements  
- ✅ **Phase 3**: Supplier management integration
- ✅ **Phase 4**: Smart inventory features and automation
  - ✅ **4A**: Transaction logging system
  - ✅ **4B**: Low stock alert system  
  - ✅ **4C**: Analytics dashboard
  - ✅ **4D**: Import/export & bulk operations

### In Progress
- 🚧 **Phase 5**: Advanced reporting and analytics
  - ⏳ **5A**: PDF report generation
  - ⏳ **5B**: Interactive charts and visualizations
  - ⏳ **5C**: Scheduled reporting system
  - ⏳ **5D**: Advanced analytics and forecasting

### Planned
- 📋 **Phase 6**: Production deployment and security
  - User authentication and role-based access
  - Multi-user support with permissions
  - Production deployment configuration
  - Advanced security and performance optimizations

## Current System Capabilities

### Inventory Management
- **Complete Product Lifecycle**: Create, read, update, delete with full audit trail
- **Advanced Search & Filtering**: Multi-field search with intelligent stock status filters
- **Bulk Operations**: Multi-product updates with transaction logging
- **Stock Adjustments**: Individual and bulk quantity changes with reason tracking

### Business Intelligence
- **Real-time Analytics**: Inventory value, stock distribution, supplier performance
- **Automated Alerts**: Configurable low stock monitoring with severity levels
- **Transaction Analytics**: Complete audit trail with filtering and product history
- **Performance Metrics**: Top products by value, attention rankings, recent activity

### Data Integration
- **Import/Export Systems**: CSV-based data exchange with external systems
- **Template Generation**: Pre-formatted import templates with current data
- **Bulk Processing**: Large-scale operations with progress tracking and validation
- **Data Integrity**: Comprehensive validation with error reporting and rollback

### Professional Features
- **Responsive Design**: Mobile-optimized interface with modern aesthetics
- **User Experience**: Intuitive navigation with context-aware quick actions
- **Error Handling**: Comprehensive validation with user-friendly messaging
- **Performance**: Optimized database queries with efficient data processing

## Code Quality & Standards

### Architecture Patterns
- **MVC Architecture**: Clean separation between models, views, and controllers
- **Database Design**: Proper relationships with foreign key constraints
- **Transaction Management**: ACID compliance with proper error handling
- **Scalable Structure**: Modular design ready for future enhancements

### Development Practices
- **Systematic Development**: Phase-by-phase implementation with clear milestones
- **Professional Standards**: Clean code with comprehensive documentation
- **Git Workflow**: Meaningful commits with descriptive messages and proper tagging
- **Testing Approach**: Feature validation before milestone completion

### Performance & Security
- **Database Optimization**: Efficient queries with proper indexing
- **Input Validation**: Comprehensive sanitization and error handling  
- **Transaction Integrity**: Atomic operations with rollback capabilities
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries

## Contributing

This project demonstrates systematic development practices and is suitable for:
- **Portfolio Projects**: Professional-grade codebase with comprehensive features
- **Learning Resource**: Step-by-step development approach with clear phases
- **Business Application**: Ready for small-to-medium business inventory management
- **Educational Use**: Modern web development practices with Flask and SQLAlchemy

### Feedback Welcome
- Report bugs or issues
- Suggest new features or improvements  
- Provide code reviews and optimization suggestions
- Share integration ideas or use cases

## License

This project is open source and available under the [MIT License](LICENSE).

---

**Current Status**: Phase 4 Complete - Professional inventory management system ready for advanced reporting and analytics implementation.

**Next Milestone**: Phase 5A - PDF Report Generation

Built with systematic development practices and professional standards.