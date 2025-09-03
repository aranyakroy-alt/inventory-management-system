from app import app, db
from models import User, UserRole

def migrate_to_phase6():
    """Add Phase 6 user tables and create admin user"""
    
    with app.app_context():
        print("🔄 Creating Phase 6 database tables...")
        
        # Create all tables (including new User table)
        db.create_all()
        print("✅ Database tables created")
        
        # Check if admin user exists
        existing_admin = User.query.filter_by(username='admin').first()
        
        if not existing_admin:
            # Create default admin user
            admin = User(
                username='admin',
                email='admin@inventory.com',
                first_name='System',
                last_name='Administrator', 
                role=UserRole.ADMIN,
                is_active=True
            )
            admin.set_password('admin123')
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Admin user created:")
            print("   Username: admin")
            print("   Password: admin123")
        else:
            print("ℹ️  Admin user already exists")
        
        print("🎉 Phase 6A migration complete!")

if __name__ == '__main__':
    migrate_to_phase6()