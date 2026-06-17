# Blog API

A RESTful Blog API built with Django REST Framework, featuring JWT authentication, posts, comments, and likes.

## Features

- **User Authentication** — JWT-based register, login, and logout with token blacklisting
- **Blog Posts** — Create, read, update, and delete posts
- **Comments** — Add and delete comments on posts
- **Likes** — Toggle likes on posts (one like per user per post)
- **User-specific Posts** — Fetch all posts by a specific user
- **CORS enabled** — Ready to connect with any frontend

## Tech Stack

- **Backend:** Django 6.0, Django REST Framework
- **Database:** PostgreSQL
- **Authentication:** djangorestframework-simplejwt
- **Other:** python-decouple, django-cors-headers, whitenoise

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|--------------|
| POST | `/register/` | Register a new user |
| POST | `/logout/` | Logout (blacklist token) |
| GET | `/blog/` | List all posts |
| POST | `/blog/` | Create a new post |
| GET | `/blog/<id>/` | Retrieve a single post |
| PUT/PATCH | `/blog/<id>/` | Update a post |
| DELETE | `/blog/<id>/` | Delete a post |
| GET | `/blog/user/<username>/` | Get all posts by a user |
| POST | `/blog/<id>/comment/` | Add a comment to a post |
| DELETE | `/comment/<id>/delete/` | Delete a comment |
| POST | `/blog/<id>/like/` | Toggle like on a post |

## Setup Instructions

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd Blog
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the project root:
```
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=your-db-name
DB_USER=your-db-user
DB_PASSWORD=your-db-password
```

### 5. Set up the database
Make sure PostgreSQL is running, then:
```bash
python manage.py migrate
```

### 6. Run the development server
```bash
python manage.py runserver
```

## Models

- **Post** — title, content, author, created_at, updated_at
- **Comment** — linked to a post and an author
- **Like** — linked to a post and a user (unique per pair)

## Author

Sumit Kumar
