from app import create_app
from extensions import db
from models import User, Habit, FocusSession

app = create_app()

with app.app_context():
    # Fresh create (does not drop existing data by default)
    db.create_all()
    print("Database tables ensured.")
    
    # Check if admin user exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created (admin / admin123).")
    else:
        print("Admin user already exists.")

    # Add default habits if none exist for admin
    if admin:
        existing_habits = Habit.query.filter_by(user_id=admin.id).count()
        if existing_habits == 0:
            default_habits = [
                ("Morning Meditation", "bi-moon-stars"),
                ("Daily Exercise", "bi-bicycle"),
                ("Deep Work (2h)", "bi-cpu"),
                ("Read 15 Pages", "bi-book")
            ]
            for name, icon in default_habits:
                h = Habit(name=name, icon=icon, user_id=admin.id)
                db.session.add(h)
            db.session.commit()
            print("Default habits added for admin.")
