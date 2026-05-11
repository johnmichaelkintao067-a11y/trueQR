from app import app, db
from models import Admin
import bcrypt

with app.app_context():
    # Delete existing admin if any
    Admin.query.delete()
    db.session.commit()
    
    # Create fresh admin
    hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin = Admin(username='admin', password_hash=hashed)
    db.session.add(admin)
    db.session.commit()
    print('✅ Admin created! Username: admin | Password: admin123')