import os
from datetime import datetime
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user
from routes.items import items_bp
from routes.auth import auth_bp, User

def create_app():
    app = Flask(__name__, static_folder="images", static_url_path="/images")

    # Configure secret key for session management
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "devsecretkeychangeme")

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.get_by_id(user_id)
    
    @login_manager.unauthorized_handler
    def unauthorized():
        return redirect(url_for("auth_bp.login"))

    # Register API routes
    app.register_blueprint(items_bp)
    app.register_blueprint(auth_bp)

    @app.get("/health")
    def health():
        return jsonify({"ok": True})

    @app.get("/")
    def home():
        if request.args.get("demo") == "1":
            return redirect(url_for("auth_bp.home", demo=1))
        return render_template("login.html")
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
