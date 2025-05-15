# create_admin.py

from models import db, User
from app import app

with app.app_context():
    db.create_all()
    admin = User(phone="998901234567", role="admin")
    admin.set_password("adminpass")
    db.session.add(admin)
    db.session.commit()
    print("✅ Администратор создан.")
