from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints
    from app.routes import init_app
    from app.routes.admin import admin_bp

    init_app(app)
    app.register_blueprint(admin_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

        # Create initial admin user if it doesn't exist
        from app.models.user import User
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',  # Add a default email
                role='admin'
            )
            admin_user.set_password('admin')  # You should change this password
            db.session.add(admin_user)
            db.session.commit()

    return app
