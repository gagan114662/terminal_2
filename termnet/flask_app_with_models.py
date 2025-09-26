import os
from datetime import datetime

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///app.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-secret-key-change-in-production"
)

# Initialize database
db = SQLAlchemy(app)

# Database Models


class User(db.Model):
    """User model for authentication and profile management"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    posts = db.relationship(
        "Post", backref="author", lazy="dynamic", cascade="all, delete-orphan"
    )
    comments = db.relationship(
        "Comment", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.username}>"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
        }


class Category(db.Model):
    """Category model for organizing posts"""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7))  # Hex color code
    icon = db.Column(db.String(50))  # Icon name/class
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    posts = db.relationship("Post", backref="category", lazy="dynamic")

    def __repr__(self):
        return f"<Category {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "color": self.color,
            "icon": self.icon,
            "post_count": self.posts.count(),
        }


# Association table for many-to-many relationship between posts and tags
post_tags = db.Table(
    "post_tags",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
    db.Column("created_at", db.DateTime, default=datetime.utcnow),
)


class Post(db.Model):
    """Post model for blog/article content"""

    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    featured_image = db.Column(db.String(255))
    status = db.Column(db.String(20), default="draft")  # draft, published, archived
    view_count = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)
    published_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Foreign keys
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))

    # Relationships
    comments = db.relationship(
        "Comment", backref="post", lazy="dynamic", cascade="all, delete-orphan"
    )
    tags = db.relationship(
        "Tag",
        secondary=post_tags,
        lazy="subquery",
        backref=db.backref("posts", lazy=True),
    )

    def __repr__(self):
        return f"<Post {self.title}>"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "excerpt": self.excerpt,
            "content": self.content,
            "featured_image": self.featured_image,
            "status": self.status,
            "view_count": self.view_count,
            "likes_count": self.likes_count,
            "published_at": self.published_at.isoformat()
            if self.published_at
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "author": self.author.username if self.author else None,
            "category": self.category.name if self.category else None,
            "tags": [tag.name for tag in self.tags],
            "comment_count": self.comments.count(),
        }


class Tag(db.Model):
    """Tag model for labeling posts"""

    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Tag {self.name}>"

    def to_dict(self):
        return {"id": self.id, "name": self.name, "slug": self.slug}


class Comment(db.Model):
    """Comment model for user interactions"""

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Foreign keys
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("comments.id"))

    # Self-referential relationship for nested comments
    replies = db.relationship(
        "Comment",
        backref=db.backref("parent", remote_side=[id]),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Comment {self.id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user": self.user.username if self.user else None,
            "post_id": self.post_id,
            "parent_id": self.parent_id,
            "is_approved": self.is_approved,
            "replies_count": self.replies.count(),
        }


class Setting(db.Model):
    """Application settings model"""

    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    value_type = db.Column(
        db.String(20), default="string"
    )  # string, integer, boolean, json
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Setting {self.key}>"

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
            "value_type": self.value_type,
            "description": self.description,
            "is_public": self.is_public,
        }


class AuditLog(db.Model):
    """Audit log for tracking system activities"""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(
        db.String(50), nullable=False
    )  # create, update, delete, login, etc.
    resource_type = db.Column(db.String(50))  # post, user, comment, etc.
    resource_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = db.relationship("User", backref="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} by user {self.user_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user": self.user.username if self.user else None,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Database initialization
def init_db():
    """Initialize database and create tables"""
    with app.app_context():
        db.create_all()

        # Create default categories if they don't exist
        if Category.query.count() == 0:
            default_categories = [
                {
                    "name": "Technology",
                    "slug": "technology",
                    "color": "#0066cc",
                    "icon": "laptop",
                },
                {
                    "name": "Business",
                    "slug": "business",
                    "color": "#28a745",
                    "icon": "briefcase",
                },
                {
                    "name": "Health",
                    "slug": "health",
                    "color": "#dc3545",
                    "icon": "heartbeat",
                },
                {
                    "name": "Travel",
                    "slug": "travel",
                    "color": "#ffc107",
                    "icon": "plane",
                },
                {
                    "name": "Education",
                    "slug": "education",
                    "color": "#6f42c1",
                    "icon": "graduation-cap",
                },
            ]

            for cat_data in default_categories:
                category = Category(**cat_data)
                db.session.add(category)

            db.session.commit()
            print("Default categories created.")

        # Create default settings if they don't exist
        if Setting.query.count() == 0:
            default_settings = [
                {
                    "key": "site_name",
                    "value": "My Flask App",
                    "value_type": "string",
                    "is_public": True,
                },
                {
                    "key": "site_description",
                    "value": "A Flask application with database models",
                    "value_type": "string",
                    "is_public": True,
                },
                {
                    "key": "posts_per_page",
                    "value": "10",
                    "value_type": "integer",
                    "is_public": False,
                },
                {
                    "key": "enable_comments",
                    "value": "true",
                    "value_type": "boolean",
                    "is_public": False,
                },
                {
                    "key": "maintenance_mode",
                    "value": "false",
                    "value_type": "boolean",
                    "is_public": False,
                },
            ]

            for setting_data in default_settings:
                setting = Setting(**setting_data)
                db.session.add(setting)

            db.session.commit()
            print("Default settings created.")


# API Routes


@app.route("/", methods=["GET"])
def home():
    """Home endpoint showing API information"""
    return jsonify(
        {
            "message": "Flask REST API with Database Models",
            "version": "1.0.0",
            "endpoints": {
                "users": "/api/users",
                "posts": "/api/posts",
                "categories": "/api/categories",
                "tags": "/api/tags",
                "comments": "/api/comments",
                "settings": "/api/settings",
                "stats": "/api/stats",
            },
        }
    )


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get application statistics"""
    return jsonify(
        {
            "users": User.query.count(),
            "posts": Post.query.count(),
            "comments": Comment.query.count(),
            "categories": Category.query.count(),
            "tags": Tag.query.count(),
        }
    )


@app.route("/api/users", methods=["GET"])
def get_users():
    """Get all users"""
    users = User.query.filter_by(is_active=True).all()
    return jsonify([user.to_dict() for user in users])


@app.route("/api/posts", methods=["GET"])
def get_posts():
    """Get all published posts"""
    posts = (
        Post.query.filter_by(status="published")
        .order_by(Post.published_at.desc())
        .all()
    )
    return jsonify([post.to_dict() for post in posts])


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Get all categories"""
    categories = Category.query.all()
    return jsonify([category.to_dict() for category in categories])


@app.route("/api/tags", methods=["GET"])
def get_tags():
    """Get all tags"""
    tags = Tag.query.all()
    return jsonify([tag.to_dict() for tag in tags])


@app.route("/api/settings", methods=["GET"])
def get_public_settings():
    """Get public settings"""
    settings = Setting.query.filter_by(is_public=True).all()
    return jsonify([setting.to_dict() for setting in settings])


@app.route("/api/posts/<int:post_id>/comments", methods=["GET"])
def get_post_comments(post_id):
    """Get comments for a specific post"""
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(
        post_id=post_id, is_approved=True, parent_id=None
    ).all()
    return jsonify([comment.to_dict() for comment in comments])


if __name__ == "__main__":
    print("Flask Application with Database Models")
    print("-" * 50)
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")
    print("-" * 50)
    print("Starting Flask application...")
    app.run(debug=True, port=5000)
