"""
Simple Blog Platform
A Flask-based blog application with SQLite database
"""

import os
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key-here-change-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db = SQLAlchemy(app)


# Database Models
class Post(db.Model):
    """Blog post model"""

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Post {self.title}>"


# Routes
@app.route("/")
def index():
    """Home page showing all blog posts"""
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template("blog_index.html", posts=posts)


@app.route("/post/<int:post_id>")
def view_post(post_id):
    """View a single blog post"""
    post = Post.query.get_or_404(post_id)
    return render_template("blog_post.html", post=post)


@app.route("/new", methods=["GET", "POST"])
def new_post():
    """Create a new blog post"""
    if request.method == "POST":
        title = request.form.get("title")
        author = request.form.get("author")
        content = request.form.get("content")

        if title and author and content:
            post = Post(title=title, author=author, content=content)
            db.session.add(post)
            db.session.commit()
            flash("Post created successfully!", "success")
            return redirect(url_for("view_post", post_id=post.id))
        else:
            flash("Please fill in all fields", "error")

    return render_template("blog_new.html")


@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    """Edit an existing blog post"""
    post = Post.query.get_or_404(post_id)

    if request.method == "POST":
        post.title = request.form.get("title")
        post.author = request.form.get("author")
        post.content = request.form.get("content")
        post.updated_at = datetime.utcnow()

        db.session.commit()
        flash("Post updated successfully!", "success")
        return redirect(url_for("view_post", post_id=post.id))

    return render_template("blog_edit.html", post=post)


@app.route("/delete/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    """Delete a blog post"""
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted successfully!", "success")
    return redirect(url_for("index"))


# Initialize database tables
def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        print("Database initialized!")


# Run the application
if __name__ == "__main__":
    # Ensure templates directory exists
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)

    # Initialize database
    init_db()

    # Add sample data if database is empty
    with app.app_context():
        if Post.query.count() == 0:
            sample_posts = [
                Post(
                    title="Welcome to Our Blog",
                    author="Admin",
                    content="This is your first blog post! You can create, edit, and delete posts using the interface above.",
                ),
                Post(
                    title="Getting Started with Flask",
                    author="Developer",
                    content="Flask is a lightweight web framework for Python. It's easy to learn and perfect for building blog platforms like this one.",
                ),
            ]
            for post in sample_posts:
                db.session.add(post)
            db.session.commit()
            print("Sample posts added!")

    # Run the app
    app.run(debug=True, port=5000)
