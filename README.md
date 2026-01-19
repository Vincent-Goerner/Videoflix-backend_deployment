# Videoflix

## 🔍 Overview
Videoflix is a Django-based, video streaming platform developed as part of the Developer Akademie program. It allows registered users to stream videos with HLS support from different categories and video resolution.

## ✨ Features

### User Authentication
- E-mail verification based registration
- Login based on JWT authentication
- Logout functionality
- Password reset function

### Video Managment
- Video Upload and management (Only superusers can upload videos via the admin panel)
- Video categorization
- different resolution options
- HLS streaming support
- Video thumbnail support

## ⚙️ Installation

### Prerequisites
#### Local Setup
- Python 3.13+
- Django 4.0+
- Django REST Framework
- Django-Cors-Headers
- SimpleJWT
- FFmpeg
- redis
- Docker 28.5.1+
- Docker Compose 2.40+

Full list: requirements.txt (Installation guide see below)

### Docker Installation
```bash
# 1. Clone the repository

git clone https://github.com/Vincent-Goerner/Videoflix-backend.git
cd Videoflix-backend

# 2. Create .env using the 'git bash' console

cd Videoflix-backend

  # Windows
  copy .env.template .env

  # Linux/Mac
  cp .env.template .env

| ⚠️IMPORTANT
| It is absolutely necessary that the .env is filled with your configurations!

# 3. Build Docker Image

docker-compose build

# 4. Start Docker Container

docker-compose up -d

# 5. Run migrations

docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

The server is accessible at http://localhost:8000.

## 🚀 API Endpoints (Examples)

### ✍️ Video Content
| Method | Endpoint                                           | Description                                                |
| ------ | ---------------------------------------------------| ---------------------------------------------------------- |
| GET    | /api/video/                                        | List all videos                                            |
| GET    | /api/video/{movie_id}/{resolution}/index.m3u8      | Retrieve a single video in a selected resolution           |
| GET    | /api/video/{movie_id}/{resolution}/{segment}/      | Retrieve a single video segment in a selected resolution   |


### 🔐 Authentication
| Method | Endpoint                                 |
| ------ | ---------------------------------------- |
| POST   | /api/register/                           |
| POST   | /api/login/                              |
| POST   | /api/logout/                             | 
| POST   | /api/token/refresh/                      |
| GET    | /api/activate/{uidb64}/{token}/          | 
| POST   | /api/password_reset/                     |
| POST   | /api/password_confirm/{uidb64}/{token}/  |


## 🚫 Security & .env

This project uses a .env file to manage environment-specific and sensitive settings such as:

#### Admin (⚠️ Required - Change these values)
- DJANGO_SUPERUSER_USERNAME
- DJANGO_SUPERUSER_PASSWORD
- DJANGO_SUPERUSER_EMAIL

#### Django (⚠️ Required - Change these values)
- SECRET_KEY
- DEBUG
- ALLOWED_HOSTS
- CSRF_TRUSTED_ORIGINS

#### Frontend URL (✅ Optional - Change if using different URL)
- FRONTEND_URL

#### Database (⚠️ Required - Change username and password)
- DB_NAME
- DB_USER
- DB_PASSWORD
- DB_HOST
- DB_PORT

#### Redis (✅ Optional - Default values work with Docker)
- REDIS_HOST
- REDIS_LOCATION
- REDIS_PORT
- REDIS_DB

#### Email Configuration (⚠️ Required - Configure your SMTP settings)
- EMAIL_HOST
- EMAIL_PORT
- EMAIL_HOST_USER
- EMAIL_HOST_PASSWORD
- EMAIL_USE_TLS
- EMAIL_USE_SSL
- DEFAULT_FROM_EMAIL

The .env file is excluded from version control (.gitignore), but a .env.template is provided as a template.
Please copy .env.template to .env and fill in your own values before running the project.

## 🔧 Development Standards

Clean Code: Methods < 14 lines

Naming: snake_case for functions and variables

No dead/commented-out code

PEP-8 Compliance: All Python files follow PEP-8 guidelines


## 📄 License

Open-source project for educational purposes. Not intended for commercial use.
