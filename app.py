import os
from flask import Flask, render_template # Render build trigger
from extensions import db, login_manager, csrf, migrate, mail
from models import User

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # --- Config ---
    db_url = os.environ.get('APP_DATABASE_URL', 'sqlite:///productivity.db')
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key'),
        SQLALCHEMY_DATABASE_URI=db_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAIL_SERVER=os.environ.get('MAIL_SERVER', 'smtp.googlemail.com'),
        MAIL_PORT=int(os.environ.get('MAIL_PORT', 587)),
        MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1'],
        MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
        MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME'))
    )

    # --- Initialize extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_datetime():
        from datetime import datetime
        return dict(datetime=datetime)

    # --- Register blueprints ---
    from blueprints.auth.routes import auth_bp
    from blueprints.dashboard.routes import dashboard_bp
    from blueprints.admin.routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # --- Error Handlers ---
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.route('/')
    def home():
        return render_template('welcome.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True),    
