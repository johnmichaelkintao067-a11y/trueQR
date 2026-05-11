from app import app, db
from models import Admin
import bcrypt

with app.app_context():
    db.create_all()
    print('✅ Tables created!')
    
    if not Admin.query.first():
        hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin = Admin(username='admin', password_hash=hashed)
        db.session.add(admin)
        db.session.commit()
        print('✅ Admin created!')
    else:
        print('ℹ️ Admin already exists!')