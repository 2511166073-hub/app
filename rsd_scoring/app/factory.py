"""
Application factory and initialization for the RSD Scoring application.
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash


db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config=None):
    """Application factory for creating the Flask app.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'rsd-scoring-secret-key-2024'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rsd.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    if config:
        app.config.update(config)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.auth.routes import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Create database tables and default admin
    with app.app_context():
        db.create_all()
        
        # Create admin if not exists
        from app.models import User
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                full_name='Administrator',
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print('Admin account created: admin / admin123')
    
    return app
