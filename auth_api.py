import os
from datetime import datetime, timedelta

from flask import Flask, jsonify, request
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-secret-key-change-in-production"
)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///auth.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get(
    "JWT_SECRET_KEY", "jwt-secret-key-change-in-production"
)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config["JWT_BLACKLIST_TOKEN_CHECKS"] = ["access", "refresh"]

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app)

blacklist = set()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
        }


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in blacklist


def create_tables():
    with app.app_context():
        db.create_all()


@app.route("/api/auth/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        if (
            not data
            or not data.get("username")
            or not data.get("email")
            or not data.get("password")
        ):
            return jsonify({"error": "Username, email, and password are required"}), 400

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if len(password) < 6:
            return (
                jsonify({"error": "Password must be at least 6 characters long"}),
                400,
            )

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 409

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        new_user = User(username=username, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        access_token = create_access_token(identity=str(new_user.id))
        refresh_token = create_refresh_token(identity=str(new_user.id))

        return (
            jsonify(
                {
                    "message": "User created successfully",
                    "user": new_user.to_dict(),
                    "access_token": access_token,
                    "refresh_token": refresh_token,
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

        if not data or not data.get("username") or not data.get("password"):
            return jsonify({"error": "Username and password are required"}), 400

        username = data.get("username")
        password = data.get("password")

        user = User.query.filter_by(username=username).first()

        if not user:
            user = User.query.filter_by(email=username).first()

        if not user or not bcrypt.check_password_hash(user.password, password):
            return jsonify({"error": "Invalid credentials"}), 401

        if not user.is_active:
            return jsonify({"error": "Account is deactivated"}), 403

        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return (
            jsonify(
                {
                    "message": "Login successful",
                    "user": user.to_dict(),
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/logout", methods=["POST"])
@jwt_required()
def logout():
    try:
        jti = get_jwt()["jti"]
        blacklist.add(jti)
        return jsonify({"message": "Successfully logged out"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    try:
        current_user_id = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user_id)
        return jsonify({"access_token": new_access_token}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/profile", methods=["GET"])
@jwt_required()
def get_profile():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"user": user.to_dict()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()

        if "email" in data:
            existing_user = User.query.filter_by(email=data["email"]).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({"error": "Email already in use"}), 409
            user.email = data["email"]

        if "username" in data:
            existing_user = User.query.filter_by(username=data["username"]).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({"error": "Username already taken"}), 409
            user.username = data["username"]

        user.updated_at = datetime.utcnow()
        db.session.commit()

        return (
            jsonify(
                {"message": "Profile updated successfully", "user": user.to_dict()}
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/change-password", methods=["POST"])
@jwt_required()
def change_password():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()

        if not data.get("current_password") or not data.get("new_password"):
            return (
                jsonify({"error": "Current password and new password are required"}),
                400,
            )

        if not bcrypt.check_password_hash(user.password, data["current_password"]):
            return jsonify({"error": "Current password is incorrect"}), 401

        if len(data["new_password"]) < 6:
            return (
                jsonify({"error": "New password must be at least 6 characters long"}),
                400,
            )

        user.password = bcrypt.generate_password_hash(data["new_password"]).decode(
            "utf-8"
        )
        user.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({"message": "Password changed successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/users", methods=["GET"])
@jwt_required()
def get_all_users():
    try:
        users = User.query.all()
        return (
            jsonify({"users": [user.to_dict() for user in users], "total": len(users)}),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/verify", methods=["GET"])
@jwt_required()
def verify_token():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({"valid": False, "error": "User not found"}), 404

        return jsonify({"valid": True, "user": user.to_dict()}), 200
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return (
        jsonify(
            {
                "message": "Authentication API",
                "endpoints": {
                    "auth": {
                        "POST /api/auth/register": "Register new user",
                        "POST /api/auth/login": "User login",
                        "POST /api/auth/logout": "User logout (requires token)",
                        "POST /api/auth/refresh": "Refresh access token",
                        "GET /api/auth/profile": "Get user profile (requires token)",
                        "PUT /api/auth/profile": "Update user profile (requires token)",
                        "POST /api/auth/change-password": "Change password (requires token)",
                        "GET /api/auth/users": "Get all users (requires token)",
                        "GET /api/auth/verify": "Verify token validity",
                    }
                },
            }
        ),
        200,
    )


@app.route("/health", methods=["GET"])
def health_check():
    return (
        jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}),
        200,
    )


if __name__ == "__main__":
    create_tables()
    app.run(debug=True, port=5001)
