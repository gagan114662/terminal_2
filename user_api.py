import os
from datetime import datetime

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(basedir, 'users.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"

db = SQLAlchemy(app)


# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
        }


# Create tables
with app.app_context():
    db.create_all()

# API Routes


@app.route("/api/users", methods=["GET"])
def get_users():
    """Get all users with optional filtering"""
    try:
        # Optional query parameters
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        is_active = request.args.get("is_active", type=lambda x: x.lower() == "true")

        query = User.query

        if is_active is not None:
            query = query.filter_by(is_active=is_active)

        # Paginate results
        users = query.paginate(page=page, per_page=per_page, error_out=False)

        return (
            jsonify(
                {
                    "users": [user.to_dict() for user in users.items],
                    "total": users.total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": users.pages,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """Get a single user by ID"""
    try:
        user = User.query.get_or_404(user_id)
        return jsonify({"user": user.to_dict()}), 200
    except Exception:
        return jsonify({"error": "User not found"}), 404


@app.route("/api/users", methods=["POST"])
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["username", "email", "password"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Check if user already exists
        if User.query.filter_by(username=data["username"]).first():
            return jsonify({"error": "Username already exists"}), 400

        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already exists"}), 400

        # Create new user
        user = User(
            username=data["username"],
            email=data["email"],
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
        )
        user.set_password(data["password"])

        db.session.add(user)
        db.session.commit()

        return (
            jsonify({"message": "User created successfully", "user": user.to_dict()}),
            201,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    """Update an existing user"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()

        # Update fields if provided
        if "username" in data:
            # Check if new username is taken
            existing = User.query.filter_by(username=data["username"]).first()
            if existing and existing.id != user_id:
                return jsonify({"error": "Username already exists"}), 400
            user.username = data["username"]

        if "email" in data:
            # Check if new email is taken
            existing = User.query.filter_by(email=data["email"]).first()
            if existing and existing.id != user_id:
                return jsonify({"error": "Email already exists"}), 400
            user.email = data["email"]

        if "password" in data:
            user.set_password(data["password"])

        if "first_name" in data:
            user.first_name = data["first_name"]

        if "last_name" in data:
            user.last_name = data["last_name"]

        if "is_active" in data:
            user.is_active = data["is_active"]

        user.updated_at = datetime.utcnow()
        db.session.commit()

        return (
            jsonify({"message": "User updated successfully", "user": user.to_dict()}),
            200,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    """Delete a user"""
    try:
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/search", methods=["GET"])
def search_users():
    """Search users by username or email"""
    try:
        query = request.args.get("q", "")
        if not query:
            return jsonify({"error": "Search query required"}), 400

        users = User.query.filter(
            db.or_(
                User.username.contains(query),
                User.email.contains(query),
                User.first_name.contains(query),
                User.last_name.contains(query),
            )
        ).all()

        return (
            jsonify({"users": [user.to_dict() for user in users], "count": len(users)}),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>/deactivate", methods=["POST"])
def deactivate_user(user_id):
    """Deactivate a user account"""
    try:
        user = User.query.get_or_404(user_id)
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.session.commit()

        return (
            jsonify(
                {"message": "User deactivated successfully", "user": user.to_dict()}
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>/activate", methods=["POST"])
def activate_user(user_id):
    """Activate a user account"""
    try:
        user = User.query.get_or_404(user_id)
        user.is_active = True
        user.updated_at = datetime.utcnow()
        db.session.commit()

        return (
            jsonify({"message": "User activated successfully", "user": user.to_dict()}),
            200,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return (
        jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}),
        200,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
