# Simple Blog Application

A fully functional blog application built with Flask, featuring user authentication and post management.

## Features

- **User Authentication**: Register, login, and logout functionality
- **Blog Posts**: Create, read, update, and delete posts
- **User Profiles**: View user profiles and their posts
- **Responsive Design**: Mobile-friendly interface
- **Clean UI**: Modern and intuitive design

## Installation

1. Install dependencies:
```bash
pip install -r blog_requirements.txt
```

2. Run the application:
```bash
python blog_app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

### First Time Setup
1. Click "Register" to create a new account
2. Fill in your username, email, and password
3. Login with your credentials

### Creating Posts
1. Once logged in, click "New Post" in the navigation
2. Enter a title and content for your blog post
3. Click "Publish Post" to save

### Managing Posts
- **View**: Click on any post title to read the full content
- **Edit**: When viewing your own posts, click "Edit" to modify
- **Delete**: Click "Delete" to remove your posts (with confirmation)

### User Profiles
- Click on any username to view their profile and posts
- Access your own profile from the navigation menu

## File Structure

```
├── blog_app.py              # Main application file
├── blog_requirements.txt    # Python dependencies
├── templates/               # HTML templates
│   ├── base.html           # Base template with navigation
│   ├── index.html          # Homepage with post list
│   ├── register.html       # Registration form
│   ├── login.html          # Login form
│   ├── create_post.html    # New post form
│   ├── view_post.html      # Single post view
│   ├── edit_post.html      # Edit post form
│   └── profile.html        # User profile page
├── static/
│   └── css/
│       └── style.css       # Application styles
└── blog.db                 # SQLite database (created automatically)
```

## Testing

Run the basic test script:
```bash
python test_blog.py
```

For manual testing:
1. Register multiple users
2. Create posts with different users
3. Test editing and deleting posts
4. Verify that users can only edit their own posts
5. Check responsive design on mobile devices

## Security Notes

- Passwords are hashed using Werkzeug's security functions
- Session management with Flask-Login
- CSRF protection through Flask's built-in security
- For production, change the SECRET_KEY in blog_app.py

## Customization

- Modify `static/css/style.css` to change the appearance
- Update templates in `templates/` folder for layout changes
- Extend models in `blog_app.py` to add more features

## Technologies Used

- **Flask**: Web framework
- **Flask-SQLAlchemy**: Database ORM
- **Flask-Login**: User session management
- **SQLite**: Database
- **HTML/CSS**: Frontend
