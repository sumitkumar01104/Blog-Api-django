# Blog API

A RESTful Blog API built with Django REST Framework — JWT auth, posts, comments and likes.
Live on Render. Interactive docs at `/api/docs/`.

## Features

- JWT authentication (register, login, refresh, logout with token blacklisting)
- Posts: create, read, update, delete (only the owner can edit or delete)
- Comments: add and delete (only your own)
- Likes: toggle, one like per user per post
- Pagination (10 posts per page)
- Swagger / ReDoc docs via drf-spectacular
- Simple built-in frontend at `/`
- CORS enabled

## Tech Stack

Django 6, Django REST Framework, PostgreSQL, SimpleJWT, drf-spectacular,
python-decouple, django-cors-headers, WhiteNoise, Gunicorn

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register/` | No | Register a new user |
| POST | `/api/token/` | No | Login, returns access + refresh |
| POST | `/api/token/refresh/` | No | Get a new access token |
| POST | `/logout/` | Yes | Blacklist refresh token (`{"refresh": "..."}`) |
| GET | `/blog/` | No | List posts (paginated, `?page=2`) |
| POST | `/blog/` | Yes | Create a post |
| GET | `/blog/<id>/` | No | Retrieve a post |
| PUT/PATCH | `/blog/<id>/` | Owner | Update a post |
| DELETE | `/blog/<id>/` | Owner | Delete a post |
| GET | `/blog/user/<username>/` | Yes | Your own posts (superuser: anyone's) |
| POST | `/blog/<id>/comment/` | Yes | Add a comment |
| DELETE | `/comment/<id>/delete/` | Owner | Delete a comment |
| POST | `/blog/<id>/like/` | Yes | Toggle like |
| GET | `/api/docs/` | No | Swagger UI (`/api/redoc/` for ReDoc) |

Send the token as `Authorization: Bearer <access_token>`.

## Local Setup

```bash
git clone https://github.com/sumitkumar01104/Blog-Api-django.git
cd Blog-Api-django

python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
cp .env.example .env         # then edit values

python manage.py migrate
python manage.py createsuperuser   # optional
python manage.py runserver
```

PostgreSQL must be running and match the values in `.env`.

## Run with Docker

```bash
cp .env.example .env         # DB_HOST is set to "db" automatically by compose
docker compose up --build
```

Migrations run automatically on start. App: http://localhost:8000
(the Docker setup uses Django's dev server — not for production).

## Environment Variables

| Variable | Required | Default |
|----------|----------|---------|
| `SECRET_KEY` | Yes | — |
| `DEBUG` | No | `False` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` | Yes | — |
| `DB_PORT` | No | `5432` |
| `DB_SSLMODE` | No | `prefer` |
| `CORS_ALLOWED_ORIGINS` | No | localhost origins |
| `CSRF_TRUSTED_ORIGINS` | No | `https://*.onrender.com` |

## Tests

```bash
python manage.py test blog
```

GitHub Actions runs migration checks and tests on every push and pull request.

## Deployment (Render)

`render.yaml` defines the web service and a PostgreSQL database.
Note: Render's free PostgreSQL expires after a limited time — create a new
database (or use an external one) if the app starts returning 500 errors.

## Models

- **Post** — title, content, author, created_at, updated_at
- **Comment** — post, author, content, created_at
- **Like** — post, user (unique per pair)

## Author

Sumit Kumar — [GitHub](https://github.com/sumitkumar01104)