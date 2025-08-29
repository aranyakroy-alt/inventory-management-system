# pdf_reports.py
# Phase 5A: Professional PDF Report Generation System

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from datetime import datetime
import io
from models import db, Product, Supplier, StockTransaction, ReorderPoint

class InventoryReportGenerator:
    """
    Professional PDF report generation for inventory management system
    Generates comprehensive business reports with charts and analytics
    """
    
    def __init__(self):
        # Company branding and settings
        self.company_name = "Professional Inventory Management"
        self.report_colors = {
            'primary': colors.HexColor('#2c3e50'),
            'secondary': colors.HexColor('#3498db'),
            'success': colors.HexColor('#27ae60'),
            'warning': colors.HexColor('#f39c12'),
            'danger': colors.HexColor('#e74c3c'),
            'light_gray': colors.HexColor('#ecf0f1'),
            'dark_gray': colors.HexColor('#7f8c8d')
        }
        
        # Initialize styles
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles for professional reports"""
        
        # Company header style
        self.styles.add(ParagraphStyle(
            name='CompanyHeader',
            parent=self.styles['Title'],
            fontSize=20,
            textColor=self.report_colors['primary'],
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        
        # Report title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=self.report_colors['secondary'],
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.report_colors['primary'],
            spaceBefore=16,
            spaceAfter=8
        ))
        
        # Metric style for KPIs
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            parent=self.styles['Normal'],
            fontSize=24,
            textColor=self.report_colors['secondary'],
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Metric label style
        self.styles.add(ParagraphStyle(
            name='MetricLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.report_colors['dark_gray'],
            alignment=TA_CENTER,
            spaceBefore=4
        ))
    
    def _create_header(self, story, report_title, report_date):
        """Create professional report header"""
        
        # Company name
        story.append(Paragraph(self.company_name, self.styles['CompanyHeader']))
        
        # Report title
        story.append(Paragraph(report_title, self.styles['ReportTitle']))
        
        # Report date and time
        date_text = f"Generated on {report_date.strftime('%B %d, %Y at %I:%M %p')}"
        story.append(Paragraph(date_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
    
    def _create_metrics_section(self, story, metrics):
        """Create KPI metrics section with professional formatting"""
        
        story.append(Paragraph("Key Performance Indicators", self.styles['SectionHeader']))
        
        # Create metrics table (2 columns)
        metrics_data = []
        metric_items = list(metrics.items())
        
        for i in range(0, len(metric_items), 2):
            row = []
            
            # Left metric
            metric1 = metric_items[i]
            left_cell = [
                Paragraph(str(metric1[1]), self.styles['MetricValue']),
                Paragraph(metric1[0], self.styles['MetricLabel'])
            ]
            row.append(left_cell)
            
            # Right metric (if exists)
            if i + 1 < len(metric_items):
                metric2 = metric_items[i + 1]
                right_cell = [
                    Paragraph(str(metric2[1]), self.styles['MetricValue']),
                    Paragraph(metric2[0], self.styles['MetricLabel'])
                ]
                row.append(right_cell)
            else:
                row.append("")  # Empty cell
            
            metrics_data.append(row)
        
        metrics_table = Table(metrics_data, colWidths=[3*inch, 3*inch])
        metrics_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, self.report_colors['light_gray'])
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 20))
    
    def _create_products_table(self, story, products, title="Product Inventory Summary"):
        """Create professional products table"""
        
        story.append(Paragraph(title, self.styles['SectionHeader']))
        
        if not products:
            story.append(Paragraph("No products found.", self.styles['Normal']))
            story.append(Spacer(1, 12))
            return
        
        # Table headers
        headers = ['Product Name', 'SKU', 'Quantity', 'Price', 'Total Value', 'Status', 'Supplier']
        
        # Table data
        table_data = [headers]
        total_value = 0
        
        for product in products:
            # Calculate stock status
            if product.quantity == 0:
                status = "Out of Stock"
                status_color = self.report_colors['danger']
            elif product.quantity < 10:
                status = "Low Stock"
                status_color = self.report_colors['warning']
            else:
                status = "In Stock"
                status_color = self.report_colors['success']
            
            # Calculate values
            product_value = product.price * product.quantity
            total_value += product_value
            
            # Get supplier name
            supplier_name = product.supplier.name if product.supplier else "No Supplier"
            
            row = [
                product.name,
                product.sku,
                str(product.quantity),
                f"${product.price:.2f}",
                f"${product_value:.2f}",
                status,
                supplier_name
            ]
            table_data.append(row)
        
        # Add total row
        table_data.append([
            "TOTAL", "", "", "", f"${total_value:.2f}", "", ""
        ])
        
        # Create table
        products_table = Table(table_data, colWidths=[1.8*inch, 0.8*inch, 0.6*inch, 0.7*inch, 0.8*inch, 0.8*inch, 1.2*inch])
        
        # Table styling
        table_style = [
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), self.report_colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 8),
            ('ALIGN', (2, 1), (4, -2), 'RIGHT'),  # Align numbers right
            ('PADDING', (0, 1), (-1, -1), 6),
            
            # Total row
            ('BACKGROUND', (-1, -1), (-1, -1), self.report_colors['light_gray']),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (4, -1), (4, -1), 'RIGHT'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 1, self.report_colors['light_gray']),
            ('LINEBELOW', (0, 0), (-1, 0), 2, self.report_colors['primary']),
        ]
        
        products_table.setStyle(TableStyle(table_style))
        story.append(products_table)
        story.append(Spacer(1, 20))
    
    def _create_alerts_table(self, story, alerts_data):
        """Create low stock alerts table"""
        
        story.append(Paragraph("Low Stock Alerts", self.styles['SectionHeader']))
        
        if not alerts_data['critical_alerts'] and not alerts_data['urgent_alerts'] and not alerts_data['warning_alerts']:
            story.append(Paragraph("✅ No active alerts - All products are well-stocked!", self.styles['Normal']))
            story.append(Spacer(1, 12))
            return
        
        # Combine all alerts
        all_alerts = alerts_data['critical_alerts'] + alerts_data['urgent_alerts'] + alerts_data['warning_alerts']
        
        # Table headers
        headers = ['Product', 'Current Stock', 'Minimum', 'Alert Level', 'Suggested Order', 'Supplier']
        table_data = [headers]
        
        for alert in all_alerts:
            product = alert['product']
            reorder_point = alert['reorder_point']
            
            # Get alert level color
            level_colors = {
                'critical': self.report_colors['danger'],
                'urgent': self.report_colors['warning'],
                'warning': colors.orange
            }
            
            row = [
                f"{product.name}\n({product.sku})",
                str(product.quantity),
                str(reorder_point.minimum_quantity),
                alert['alert_level'].upper(),
                str(alert['suggested_order']),
                product.supplier.name if product.supplier else "No Supplier"
            ]
            table_data.append(row)
        
        # Create table
        alerts_table = Table(table_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch, 1.2*inch])
        
        # Table styling
        alerts_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), self.report_colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (1, 1), (4, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, self.report_colors['light_gray']),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(alerts_table)
        story.append(Spacer(1, 20))
    
    def _create_suppliers_section(self, story, suppliers_data):
        """Create suppliers performance section"""
        
        story.append(Paragraph("Supplier Performance Analysis", self.styles['SectionHeader']))
        
        if not suppliers_data:
            story.append(Paragraph("No supplier data available.", self.styles['Normal']))
            story.append(Spacer(1, 12))
            return
        
        headers = ['Supplier Name', 'Products', 'Total Stock', 'Inventory Value', 'Contact']
        table_data = [headers]
        
        for supplier, product_count, total_stock, total_value in suppliers_data:
            contact_info = []
            if supplier.contact_person:
                contact_info.append(supplier.contact_person)
            if supplier.email:
                contact_info.append(supplier.email)
            if supplier.phone:
                contact_info.append(supplier.phone)
            
            contact_text = "\n".join(contact_info) if contact_info else "No contact info"
            
            row = [
                supplier.name,
                str(product_count),
                str(total_stock or 0),
                f"${total_value or 0:.2f}",
                contact_text
            ]
            table_data.append(row)
        
        suppliers_table = Table(table_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 1*inch, 1.8*inch])
        suppliers_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), self.report_colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (1, 1), (3, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, self.report_colors['light_gray']),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(suppliers_table)
        story.append(Spacer(1, 20))
    
    def generate_inventory_summary_report(self):
        """Generate comprehensive inventory summary report"""
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Story container
        story = []
        
        # Report header
        report_date = datetime.now()
        self._create_header(story, "Inventory Summary Report", report_date)
        
        # Gather data
        total_products = Product.query.count()
        total_suppliers = Supplier.query.count()
        total_transactions = StockTransaction.query.count()
        
        products_with_stock = Product.query.filter(Product.quantity > 0).count()
        out_of_stock_products = Product.query.filter(Product.quantity == 0).count()
        low_stock_products = Product.query.filter(Product.quantity > 0, Product.quantity < 10).count()
        
        # Calculate total inventory value
        inventory_value_query = db.session.query(db.func.sum(Product.price * Product.quantity)).scalar()
        total_inventory_value = inventory_value_query if inventory_value_query else 0.0
        
        # Active alerts
        alerts_query = db.session.query(ReorderPoint, Product).join(Product).filter(
            ReorderPoint.is_active == True,
            Product.quantity < ReorderPoint.minimum_quantity
        )
        
        critical_alerts = alerts_query.filter(Product.quantity == 0).count()
        urgent_alerts = alerts_query.filter(
            Product.quantity > 0,
            Product.quantity < ReorderPoint.minimum_quantity * 0.5
        ).count()
        warning_alerts = alerts_query.filter(
            Product.quantity >= ReorderPoint.minimum_quantity * 0.5,
            Product.quantity < ReorderPoint.minimum_quantity
        ).count()
        
        total_active_alerts = critical_alerts + urgent_alerts + warning_alerts
        
        # Create KPI metrics
        metrics = {
            "Total Products": total_products,
            "Total Suppliers": total_suppliers,
            "Inventory Value": f"${total_inventory_value:,.2f}",
            "Products in Stock": products_with_stock,
            "Out of Stock": out_of_stock_products,
            "Low Stock Items": low_stock_products,
            "Active Alerts": total_active_alerts,
            "Total Transactions": total_transactions
        }
        
        self._create_metrics_section(story, metrics)
        
        # Get top products by value
        top_products = db.session.query(Product).filter(Product.quantity > 0).order_by(
            (Product.price * Product.quantity).desc()
        ).limit(20).all()
        
        self._create_products_table(story, top_products, "Top Products by Inventory Value")
        
        # Page break for next section
        story.append(PageBreak())
        
        # Get alerts data
        alerts_data = {
            'critical_alerts': [{'product': p, 'reorder_point': rp, 'alert_level': 'critical', 'suggested_order': rp.suggested_order_amount} 
                              for rp, p in alerts_query.filter(Product.quantity == 0).all()],
            'urgent_alerts': [{'product': p, 'reorder_point': rp, 'alert_level': 'urgent', 'suggested_order': rp.suggested_order_amount}
                            for rp, p in alerts_query.filter(Product.quantity > 0, Product.quantity < ReorderPoint.minimum_quantity * 0.5).all()],
            'warning_alerts': [{'product': p, 'reorder_point': rp, 'alert_level': 'warning', 'suggested_order': rp.suggested_order_amount}
                             for rp, p in alerts_query.filter(Product.quantity >= ReorderPoint.minimum_quantity * 0.5, Product.quantity < ReorderPoint.minimum_quantity).all()]
        }
        
        self._create_alerts_table(story, alerts_data)
        
        # Get supplier data
        suppliers_data = db.session.query(
            Supplier, 
            db.func.count(Product.id).label('product_count'),
            db.func.sum(Product.quantity).label('total_stock'),
            db.func.sum(Product.price * Product.quantity).label('total_value')
        ).outerjoin(Product).group_by(Supplier.id).having(
            db.func.count(Product.id) > 0
        ).order_by(db.func.sum(Product.price * Product.quantity).desc()).limit(10).all()
        
        self._create_suppliers_section(story, suppliers_data)
        
        # Footer
        story.append(Spacer(1, 30))
        footer_text = f"Report generated by {self.company_name} | {report_date.strftime('%B %d, %Y at %I:%M %p')}"
        story.append(Paragraph(footer_text, self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF data
        buffer.seek(0)
        return buffer
    
    def generate_low_stock_report(self):
        """Generate focused low stock alerts report"""
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        story = []
        
        report_date = datetime.now()
        self._create_header(story, "Low Stock Alert Report", report_date)
        
        # Get all alerts
        alerts_query = db.session.query(ReorderPoint, Product).join(Product).filter(
            ReorderPoint.is_active == True,
            Product.quantity < ReorderPoint.minimum_quantity
        )
        
        alerts_data = {
            'critical_alerts': [{'product': p, 'reorder_point': rp, 'alert_level': 'critical', 'suggested_order': rp.suggested_order_amount} 
                              for rp, p in alerts_query.filter(Product.quantity == 0).all()],
            'urgent_alerts': [{'product': p, 'reorder_point': rp, 'alert_level': 'urgent', 'suggested_order': rp.suggested_order_amount}
                            for rp, p in alerts_query.filter(Product.quantity > 0, Product.quantity < ReorderPoint.minimum_quantity * 0.5).all()],
            'warning_alerts': [{'product': p, 'reorder_point': rp, 'alert_level': 'warning', 'suggested_order': rp.suggested_order_amount}
                             for rp, p in alerts_query.filter(Product.quantity >= ReorderPoint.minimum_quantity * 0.5, Product.quantity < ReorderPoint.minimum_quantity).all()]
        }
        
        total_alerts = len(alerts_data['critical_alerts']) + len(alerts_data['urgent_alerts']) + len(alerts_data['warning_alerts'])
        
        # KPI metrics for alerts
        metrics = {
            "Total Alerts": total_alerts,
            "Critical (Out of Stock)": len(alerts_data['critical_alerts']),
            "Urgent (Very Low)": len(alerts_data['urgent_alerts']),
            "Warning (Below Min)": len(alerts_data['warning_alerts'])
        }
        
        self._create_metrics_section(story, metrics)
        self._create_alerts_table(story, alerts_data)
        
        # Calculate total suggested order value
        total_order_value = 0
        for alert_list in alerts_data.values():
            for alert in alert_list:
                suggested_qty = alert['suggested_order']
                product_price = alert['product'].price
                total_order_value += suggested_qty * product_price
        
        if total_order_value > 0:
            story.append(Paragraph("Reorder Summary", self.styles['SectionHeader']))
            summary_text = f"<b>Total Suggested Reorder Value: ${total_order_value:,.2f}</b>"
            story.append(Paragraph(summary_text, self.styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Footer
        story.append(Spacer(1, 30))
        footer_text = f"Report generated by {self.company_name} | {report_date.strftime('%B %d, %Y at %I:%M %p')}"
        story.append(Paragraph(footer_text, self.styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_supplier_report(self):
        """Generate comprehensive supplier performance report"""
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        story = []
        
        report_date = datetime.now()
        self._create_header(story, "Supplier Performance Report", report_date)
        
        # Get all supplier data
        suppliers_data = db.session.query(
            Supplier, 
            db.func.count(Product.id).label('product_count'),
            db.func.sum(Product.quantity).label('total_stock'),
            db.func.sum(Product.price * Product.quantity).label('total_value')
        ).outerjoin(Product).group_by(Supplier.id).order_by(
            db.func.sum(Product.price * Product.quantity).desc()
        ).all()
        
        # Calculate metrics
        total_suppliers = len(suppliers_data)
        suppliers_with_products = len([s for s in suppliers_data if s[1] > 0])  # product_count > 0
        total_supplier_value = sum(s[3] or 0 for s in suppliers_data)
        
        metrics = {
            "Total Suppliers": total_suppliers,
            "Active Suppliers": suppliers_with_products,
            "Total Supplier Value": f"${total_supplier_value:,.2f}",
            "Average per Supplier": f"${total_supplier_value/max(suppliers_with_products, 1):,.2f}"
        }
        
        self._create_metrics_section(story, metrics)
        
        # Active suppliers section
        active_suppliers = [s for s in suppliers_data if s[1] > 0]
        if active_suppliers:
            self._create_suppliers_section(story, active_suppliers)
        
        # Inactive suppliers
        inactive_suppliers = [s for s in suppliers_data if s[1] == 0]
        if inactive_suppliers:
            story.append(Paragraph("Inactive Suppliers (No Products)", self.styles['SectionHeader']))
            
            headers = ['Supplier Name', 'Contact Person', 'Email', 'Phone']
            table_data = [headers]
            
            for supplier, _, _, _ in inactive_suppliers:
                row = [
                    supplier.name,
                    supplier.contact_person or "Not provided",
                    supplier.email or "Not provided", 
                    supplier.phone or "Not provided"
                ]
                table_data.append(row)
            
            inactive_table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1.8*inch, 1.2*inch])
            inactive_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.report_colors['dark_gray']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, self.report_colors['light_gray']),
            ]))
            
            story.append(inactive_table)
            story.append(Spacer(1, 20))
        
        # Footer
        story.append(Spacer(1, 30))
        footer_text = f"Report generated by {self.company_name} | {report_date.strftime('%B %d, %Y at %I:%M %p')}"
        story.append(Paragraph(footer_text, self.styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer

# Utility functions for easy integration
def generate_inventory_summary_pdf():
    """Generate inventory summary PDF report"""
    generator = InventoryReportGenerator()
    return generator.generate_inventory_summary_report()

def generate_low_stock_pdf():
    """Generate low stock alerts PDF report"""
    generator = InventoryReportGenerator()
    return generator.generate_low_stock_report()

def generate_supplier_performance_pdf():
    """Generate supplier performance PDF report"""
    generator = InventoryReportGenerator()
    return generator.generate_supplier_report()