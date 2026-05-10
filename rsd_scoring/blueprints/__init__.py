"""
Blueprints package for RSD Scoring Application
"""
from .auth import auth_bp
from .main import main_bp

__all__ = ['auth_bp', 'main_bp']
