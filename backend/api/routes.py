"""
API Routes Module

This module registers all API blueprints.
"""

from flask import Blueprint
from .sheet_music import sheet_music_bp

# Create a main API blueprint
api_bp = Blueprint('api', __name__)

# Register blueprints
api_bp.register_blueprint(sheet_music_bp, url_prefix='/sheet-music') 