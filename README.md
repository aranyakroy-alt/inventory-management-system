# Professional Inventory Management System

A comprehensive Flask-based inventory management system built with a systematic, phase-by-phase approach. Features advanced product management, supplier relationships, search functionality, stock filtering, and real-time inventory tracking.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v2.0+-green.svg)
![SQLite](https://img.shields.io/badge/sqlite-v3+-orange.svg)
![Status](https://img.shields.io/badge/status-Phase%203%20Complete-success.svg)

## Features

### Phase 1: Foundation (Complete)
- Professional Flask web application
- SQLite database with SQLAlchemy ORM
- Responsive, modern UI design
- Basic product CRUD operations
- Stock level tracking with visual indicators

### Phase 2: Advanced Operations (Complete)
- **Advanced Search**: Multi-field search across name, SKU, and description
- **Smart Filtering**: Filter by stock status (All/In Stock/Low Stock/Out of Stock)
- **Quick Stock Adjustments**: +/- buttons for instant inventory updates
- **Product Management**: Full edit/delete functionality with confirmations
- **Professional UI**: Mobile-responsive design with modern styling

### Phase 3: Supplier Management (Complete)
- **Supplier Database**: Complete supplier information management
- **Supplier CRUD**: Add, edit, delete, and view suppliers with contact details
- **Product-Supplier Relationships**: Link products to suppliers with dropdown selection
- **Integrated Management**: Supplier information displayed in product listings
- **Safety Features**: Prevent deletion of suppliers with assigned products
- **Contact Management**: Store supplier contact person, email, phone, and address

### Phase 4: Smart Inventory Features (Planned)
- Transaction logging (stock in/out movements)
- Low stock alerts and reorder points
- Stock movement history
- Automated reorder suggestions

## Technology Stack

- **Backend**: Python Flask, SQLAlchemy ORM
- **Database**: SQLite (development), easily upgradeable to PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript (ES6)
- **Styling**: Custom responsive CSS with modern design patterns
- **Version Control**: Git with systematic commit history

## Installation & Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/inventory-management-system.git
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

## Usage

### Product Management
- **Add Products**: Professional forms with validation and supplier selection
- **Search Products**: Real-time search across multiple fields
- **Filter Products**: Smart filtering by stock levels
- **Stock Adjustments**: Quick +/- controls for inventory updates
- **Edit/Delete**: Full CRUD operations with confirmations

### Supplier Management
- **Add Suppliers**: Complete supplier information forms
- **Manage Contacts**: Store contact person, email, phone, and address
- **Assign Products**: Link products to suppliers during creation/editing
- **View Relationships**: See which products each supplier provides
- **Safety Controls**: Protected deletion prevents data integrity issues

### Professional Features
- Responsive design for desktop and mobile
- Advanced error handling and user feedback
- Professional UI with consistent styling
- Real-time stock status indicators
- Integrated supplier-product relationships

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
```

## Project Structure

```
inventory_system/
├── app.py              # Main Flask application (10 routes)
├── models.py           # Database models (Product, Supplier)
├── templates/          # Jinja2 templates
│   ├── base.html       # Master template with navigation
│   ├── index.html      # Homepage
│   ├── add_product.html# Product creation with supplier selection
│   ├── edit_product.html# Product editing with supplier selection
│   ├── products.html   # Advanced product listing with supplier info
│   ├── suppliers.html  # Supplier management page
│   ├── add_supplier.html# Supplier creation form
│   └── edit_supplier.html# Supplier editing form
├── static/
│   └── style.css       # Professional styling
└── requirements.txt    # Dependencies
```

## Development Phases

This project follows a systematic development approach:

- **Phase 1**: Foundation setup and basic functionality
- **Phase 2**: Advanced inventory operations and UI enhancements  
- **Phase 3**: Supplier management integration (Current: Complete)
- **Phase 4**: Smart inventory features and automation
- **Phase 5**: Reporting and analytics
- **Phase 6**: Production deployment and optimization

## Future Enhancements

- Advanced reporting and analytics
- Automated low-stock alerts
- Barcode scanning integration
- Multi-user authentication
- API endpoints for external integration
- Advanced supplier management features

## Professional Development

This project demonstrates:
- **Systematic Development**: Phase-by-phase feature implementation
- **Professional Standards**: Clean code, proper documentation, comprehensive testing
- **Modern Practices**: Git version control, responsive design, error handling
- **Scalable Architecture**: Modular design ready for future enhancements
- **Database Design**: Proper relationships and data integrity

## Contributing

This is a learning project, but feedback and suggestions are welcome! Please feel free to:
- Report bugs or issues
- Suggest new features
- Provide code reviews
- Share improvement ideas

## License

This project is open source and available under the [MIT License](LICENSE).

---

**Built with systematic development practices and professional standards**