# Caldwell Symphony Backend

A FastAPI backend API for a local community platform supporting the Caldwell Symphony in Caldwell, Idaho. This project demonstrates modern async Python backend development with authentication, role-based access control, threaded discussions, and media management.

> **Note**: This is a portfolio project built to showcase full-stack backend development skills, clean architecture, testing practices, and real-world API design.

## Features

- **Authentication & Authorization** — JWT-based authentication with role-based access control (User / Admin)
- **Threaded Comments** — Full support for nested replies and comment threads with soft/hard delete options
- **Media Uploads** — Image and video uploads with ownership validation, powered by Supabase Storage
- **Admin Tools** — Dedicated admin endpoints for user and comment moderation
- **Robust Error Handling** — Centralized exception handling with consistent API error responses
- **Database Migrations** — Proper schema management using Alembic
- **Async Architecture** — Built with async SQLAlchemy 2.0 and FastAPI for high performance
- **Comprehensive Testing** — Pytest-based test suite with reusable fixtures and admin/user client helpers

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (async SQLAlchemy 2.0)
- **Migrations**: Alembic
- **Authentication**: JWT + OAuth2 Password Flow
- **Storage**: Supabase Storage
- **Testing**: pytest + HTTPX
- **Validation**: Pydantic v2
- **Python**: 3.12+

## Project Structure
caldwell-symphony-backend/
├── app/
│   ├── models/           # SQLAlchemy models
│   ├── routers/          # API route handlers
│   ├── schemas/          # Pydantic request/response models
│   ├── dependencies.py   # Reusable dependencies (auth, DB, etc.)
│   ├── exceptions.py     # Custom exception classes
│   ├── config.py         # Settings and configuration
│   ├── database.py       # Database engine and session setup
│   └── main.py           # FastAPI application entrypoint
├── alembic/              # Database migrations
│   └── versions/
├── tests/                # Test suite with fixtures
├── .env                  # Environment variables (not committed)
├── alembic.ini
├── requirements.txt
└── README.md

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL database (local or via Supabase)
- Supabase account (for Storage)

### Installation

1. Clone the repository

```bash
git clone <your-repo-url>
cd caldwell-symphony-backend

2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

4. Set up environment variables
Create a .env file in the root directory (see the Environment Variables section below).

5. Run database migrations
alembic upgrade head

6. Start the development server
uvicorn app.main:app --reload

The API will be available at http://127.0.0.1:8000


Environment Variables
Create a .env file with the following variables:

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/caldwell_symphony

# JWT
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Supabase Storage
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_BUCKET=media

Important: Never commit your .env file or real credentials to version control.

API Documentation
Interactive API documentation is available when the server is running:

Swagger UI: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc

Testing
Run the test suite with:

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run only auth tests
pytest tests/test_auth.py -v

# Run only comment tests
pytest tests/test_comments.py -v

# Run only admin tests
pytest tests/test_admin.py -v

