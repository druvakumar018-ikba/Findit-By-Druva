import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from config import Config
from models import db
from database import seed_database
from utils.auth_schema import migrate_phone_auth_schema, migrate_item_reporter_schema

# Blueprints
from routes.auth import auth_bp
from routes.items import items_bp
from routes.claims import claims_bp
from routes.admin import admin_bp
from routes.notifications import notifications_bp
from routes.contact import contact_bp

def create_app(config_class=Config):
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_class)
    if not app.config.get('SECRET_KEY') or not app.config.get('JWT_SECRET_KEY'):
        raise RuntimeError('SECRET_KEY and JWT_SECRET_KEY must be configured in production.')
    
    # Configure Database URI
    app.config['SQLALCHEMY_DATABASE_URI'] = config_class.get_database_uri()
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'items'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'claims'), exist_ok=True)
    
    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(claims_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(contact_bp)
    
    # Route to serve uploaded files
    @app.route('/uploads/<path:filename>')
    def serve_uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        
    # Health check route
    @app.route('/api/health', methods=['GET'])
    def health_check():
        db_type = 'MySQL' if 'mysql' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'
        return jsonify({
            'status': 'online',
            'app_name': 'FindIt - Smart Lost and Found Platform API',
            'version': '1.0.0',
            'database': db_type
        }), 200

    # Global error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({'success': False, 'message': 'Endpoint not found.'}), 404

    @app.errorhandler(413)
    def request_entity_too_large_error(error):
        return jsonify({'success': False, 'message': 'File upload exceeds maximum allowed size (5MB).'}), 413

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Internal server error occurred.'}), 500

    # Create tables and seed data automatically on startup
    with app.app_context():
        migrate_phone_auth_schema(db.engine)
        migrate_item_reporter_schema(db.engine)
        db.create_all()
        seed_database()

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    print(f"\n=======================================================")
    print(f"🚀 FindIt Backend REST API running on http://localhost:{port}")
    print(f"=======================================================\n")
    app.run(host='0.0.0.0', port=port, debug=True)
