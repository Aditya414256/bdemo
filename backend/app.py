import os
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from .config import Config
from .models import db
from .routes import auth_bp, medicines_bp, orders_bp, pharmacy_bp, admin_bp
from .utils.responses import api_response

def create_app(config_class=Config):
    """Application factory for the MediFind backend."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Database
    db.init_app(app)

    # Configure CORS for frontend development
    allowed_origins = app.config.get('FRONTEND_ORIGINS', ['*'])
    CORS(
        app,
        resources={r"/*": {"origins": allowed_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"]
    )

    # Ensure upload directory exists
    upload_dir = Path(app.config['UPLOAD_FOLDER'])
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(medicines_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(pharmacy_bp)
    app.register_blueprint(admin_bp)

    # Health check route
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return api_response(True, "MediFind API is running smoothly.", data={'status': 'healthy'}, status_code=200)

    # Frontend Static Serving
    project_root = Path(__file__).resolve().parent.parent

    @app.route('/')
    def serve_index():
        return send_from_directory(str(project_root), 'HomePage.html')

    @app.route('/<path:filename>')
    def serve_frontend(filename):
        # Don't intercept API routes
        if filename.startswith('api/'):
            return api_response(False, "API route not found.", status_code=404)
        target = project_root / filename
        if target.exists() and target.is_file():
            return send_from_directory(str(project_root), filename)
        return send_from_directory(str(project_root), 'HomePage.html')

    # Global Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        return api_response(False, "Bad Request: " + str(error.description if hasattr(error, 'description') else error), status_code=400)

    @app.errorhandler(404)
    def not_found(error):
        return api_response(False, "Requested endpoint or resource was not found.", status_code=404)

    @app.errorhandler(405)
    def method_not_allowed(error):
        return api_response(False, "HTTP method not allowed for this endpoint.", status_code=405)

    @app.errorhandler(413)
    def file_too_large(error):
        return api_response(False, "Uploaded file exceeds maximum allowed size (5MB).", status_code=413)

    @app.errorhandler(500)
    def internal_server_error(error):
        return api_response(False, "An unexpected internal server error occurred.", status_code=500)

    # Automatically create database tables when initializing
    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')
    print(f"\n========================================================")
    print(f" MediFind Backend Server running on http://127.0.0.1:{port}")
    print(f" CORS Allowed Origins: {app.config.get('FRONTEND_ORIGINS')}")
    print(f"========================================================\n")
    app.run(host='0.0.0.0', port=port, debug=debug)
