import os
from datetime import datetime, timedelta

from flask import Flask, jsonify, request
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (JWTManager, create_access_token,
                                get_jwt_identity, jwt_required)
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get(
    "JWT_SECRET_KEY", "dev-secret-key-change-in-production"
)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self, include_email=True):
        data = {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
        }
        if include_email:
            data["email"] = self.email
        return data

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


# Create tables
with app.app_context():
    db.create_all()


# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request"}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500


# Authentication endpoints
@app.route("/api/auth/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["username", "email", "password"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        # Check if user already exists
        if User.query.filter_by(username=data["username"]).first():
            return jsonify({"error": "Username already exists"}), 409

        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already exists"}), 409

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

        # Generate access token
        access_token = create_access_token(identity=user.id)

        return (
            jsonify(
                {
                    "message": "User registered successfully",
                    "user": user.to_dict(),
                    "access_token": access_token,
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        if not data.get("username") or not data.get("password"):
            return jsonify({"error": "Username and password are required"}), 400

        # Find user by username or email
        user = User.query.filter(
            (User.username == data["username"]) | (User.email == data["username"])
        ).first()

        if not user or not user.check_password(data["password"]):
            return jsonify({"error": "Invalid credentials"}), 401

        if not user.is_active:
            return jsonify({"error": "Account is deactivated"}), 403

        # Generate access token
        access_token = create_access_token(identity=user.id)

        return (
            jsonify(
                {
                    "message": "Login successful",
                    "user": user.to_dict(),
                    "access_token": access_token,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# User management endpoints
@app.route("/api/users", methods=["GET"])
@jwt_required()
def get_users():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        users = User.query.paginate(page=page, per_page=per_page, error_out=False)

        return (
            jsonify(
                {
                    "users": [
                        user.to_dict(include_email=False) for user in users.items
                    ],
                    "total": users.total,
                    "pages": users.pages,
                    "current_page": page,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        current_user_id = get_jwt_identity()

        # Only show email if it's the current user or an admin (simplified for this example)
        include_email = current_user_id == user_id

        return jsonify(user.to_dict(include_email=include_email)), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    try:
        current_user_id = get_jwt_identity()

        # Users can only update their own profile (simplified authorization)
        if current_user_id != user_id:
            return jsonify({"error": "Unauthorized"}), 403

        user = User.query.get_or_404(user_id)
        data = request.get_json()

        # Update allowed fields
        if "email" in data:
            # Check if email is already taken
            existing_user = User.query.filter_by(email=data["email"]).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({"error": "Email already exists"}), 409
            user.email = data["email"]

        if "first_name" in data:
            user.first_name = data["first_name"]

        if "last_name" in data:
            user.last_name = data["last_name"]

        if "password" in data:
            user.set_password(data["password"])

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
@jwt_required()
def delete_user(user_id):
    try:
        current_user_id = get_jwt_identity()

        # Users can only delete their own account (simplified authorization)
        if current_user_id != user_id:
            return jsonify({"error": "Unauthorized"}), 403

        user = User.query.get_or_404(user_id)

        # Soft delete - just deactivate the account
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({"message": "User account deactivated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/me", methods=["GET"])
@jwt_required()
def get_current_user():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)

        return jsonify(user.to_dict()), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Health check endpoint
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "User Management API"}), 200


if __name__ == "__main__":
    print("User Management REST API")
    print("-" * 40)
    print("Available endpoints:")
    print("POST   /api/auth/register - Register new user")
    print("POST   /api/auth/login - Login user")
    print("GET    /api/users - Get all users (requires auth)")
    print("GET    /api/users/<id> - Get specific user (requires auth)")
    print("PUT    /api/users/<id> - Update user (requires auth)")
    print("DELETE /api/users/<id> - Delete user (requires auth)")
    print("GET    /api/users/me - Get current user (requires auth)")
    print("GET    /api/health - Health check")
    print("-" * 40)
    app.run(debug=True, port=5001)
