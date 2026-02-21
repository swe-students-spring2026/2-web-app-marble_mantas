from flask import Flask, jsonify
from routes.items import items_bp


def create_app():
    app = Flask(__name__)

    # Register API routes
    app.register_blueprint(items_bp)

    @app.get("/health")
    def health():
        return jsonify({"ok": True})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)