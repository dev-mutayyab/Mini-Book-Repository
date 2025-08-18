## Repository for Books - FastAPI Backend

### Overview

Backend service for managing a repository of books with authentication, CSV uploads, and Redis-backed upload status tracking. Built with `FastAPI`, `SQLAlchemy`, `Pydantic v2`, and `Redis`.

### Features

- User registration, email token verification, login, refresh tokens
- Password change, forgot password with OTP verification
- CRUD for books with search and pagination
- CSV upload for bulk book creation, processed in the background
- Upload processing status stored in Redis
- Structured JSON responses and rotating file logs

### Tech Stack

- **API**: `FastAPI`
- **ORM**: `SQLAlchemy 2`
- **Validation/Settings**: `Pydantic v2`, `pydantic-settings`
- **Auth**: `python-jose`, `passlib[bcrypt]`
- **Background/Status**: `Redis`
- **Server**: `uvicorn`
- **DB**: SQLite (default) via `DATABASE_URL`

### Requirements

- Python 3.10+
- Redis running locally at `localhost:6379` (default). You can adjust in `app/utils/app_redis.py`.

### Important: Redis on Windows

If you're on Windows, install Redis from the community-maintained Windows port and ensure Redis is running before starting this app. Otherwise, the app will fail to start because it pings Redis on startup.

- Download Redis for Windows: [tporadowski/redis Releases](https://github.com/tporadowski/redis/releases)
- After extracting, start the server by running `redis-server.exe`
- Optional: verify with `redis-cli.exe ping` and expect `PONG`

### Getting Started

1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. Create `.env` (optional but recommended)

```env
# app/core/config.py reads these via pydantic-settings
DATABASE_URL=sqlite:///./books_repository.db
JWT_SECRET=change_me_to_a_long_random_value
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=1
```

4. Initialize the database (creates tables in `books_repository.db`)

```powershell
python -m app.db.init_db
```

5. Run the server

```powershell
uvicorn app.main:app --reload
```

- Open the interactive API docs: [OpenAPI docs](http://127.0.0.1:8000/docs)

### API Overview

Auth

- POST `/register`
- GET `/verify-email/{token}`
- POST `/login`
- POST `/refresh`
- PUT `/forgot-password`
- POST `/change_password`
- POST `/verify-otp`

Books

- POST `/books`
- PUT `/books/{book_id}`
- GET `/books/{book_id}`
- DELETE `/books/{book_id}`
- GET `/books` — supports `search`, `offset`, `limit`
- POST `/books/upload` — CSV upload
- GET `/books/upload/{upload_id}` — upload status

CSV Upload Format
The CSV must include headers: `title,author,price,publication_date`.
Example row:

```csv
title,author,price,publication_date
Clean Code,Robert C. Martin,29.99,2008-08-11
```

### Project Structure

```
app/
  main.py
  core/
    config.py
    security.py
  db/
    session.py
    init_db.py
  dependencies/
    auth.py
  models/
    user.py
    otp.py
    books.py
  routes/
    auth.py
    books.py
  schemas/
    auth.py
    books.py
  services/
    otp.py
    books.py
  utils/
    app_redis.py
    error_logger.py
    response.py
uploads/
logs/
books_repository.db (created after init)
```

### Design decisions and justifications

- **Database (SQLite + SQLAlchemy ORM)**: Chosen for simplicity and zero-config local development. It satisfies the task’s requirement for a lightweight store while keeping the code portable to production databases by only changing `DATABASE_URL`. SQLAlchemy provides robust models and migrations can be added later if needed.

- **Authentication (JWT with access/refresh tokens)**: Implemented using `python-jose` and `passlib[bcrypt]`. JWTs are stateless and fit microservices well. Access tokens are short-lived, refresh tokens allow seamless re-authentication without keeping server-side sessions. This keeps the service horizontally scalable and easy to integrate with gateways.

- **Authorization flow**: Endpoints that mutate data (create/update/delete, uploads) require a valid Bearer token via a dependency (`get_current_user`). The token’s subject is the user’s email, verified against the DB.

- **Book model**: Uses UUID string primary key to avoid collisions and to be opaque across services. Fields match the task: `id`, `title`, `author`, `price`, `publication_date`, `created_at`, `updated_at`.

- **Pagination strategy (offset/limit)**: Implemented as `GET /books?offset=0&limit=10` with optional `search` query. Offset/limit is simple to reason about, widely supported, and adequate for the dataset size in this exercise. It pairs well with SQLAlchemy’s `offset/limit` and keeps the API intuitive. For very large datasets or stable paging under concurrent writes, cursor-based pagination can be introduced later.

- **Search**: Case-insensitive match on `title` or `author` using `ILIKE` with `%query%`. This is straightforward and efficient for small-to-medium datasets. It fulfills `GET /books?search=...` requirement.

- **File upload and background processing**: CSV uploads are accepted at `POST /books/upload` and processed asynchronously using FastAPI `BackgroundTasks`. This prevents request timeouts and keeps the API responsive for large files. Processing status is tracked in Redis and surfaced via `GET /books/upload/{upload_id}`. The choice of Redis provides a lightweight, reliable, and fast mechanism to share progress and errors between the background task and API.

- **CSV validation and error handling**: The processor validates required headers, checks duplicates by title, enforces non-negative price, and parses ISO `publication_date`. Per-row errors are accumulated and exposed via the status endpoint. API responses are normalized using helper functions returning `{status_code, message, data}` for consistency.

- **Pydantic v2 schemas**: Request/response models (`CreateBook`, `UpdateBook`, `ShowBook`, `ShowBookList`, auth schemas) provide type safety and automatic validation. `from_attributes = True` enables ORM object serialization.

- **OpenAPI documentation**: FastAPI auto-generates docs at `/docs` based on path operation signatures and Pydantic models, fulfilling the documentation requirement.

- **Logging**: Rotating file and console logging via `app/utils/error_logger.py` for observability of background processing and API actions.

- **Why Redis (and why now)**: The app pings Redis on startup to ensure availability, since CSV processing status relies on it. Using Redis avoids coupling status to a single process and enables scaling the worker/API separately in the future.

### Requirements checklist (mapped to this repo)

- **Core CRUD**:
  - Model: `app/models/books.py` contains `Books` with `id`, `title`, `author`, `price`, `publication_date` (equivalent to "published_date" in the task), `created_at`, `updated_at`.
  - Endpoints: `POST /books`, `GET /books/{book_id}`, `PUT /books/{book_id}`, `DELETE /books/{book_id}`, `GET /books` in `app/routes/books.py`.
- **Search & Pagination**:
  - `GET /books?search=...&offset=...&limit=...` with case-insensitive match on title/author and offset/limit pagination.
- **Authentication**:
  - JWT-based via `app/core/security.py`; protected routes depend on `get_current_user` (`app/dependencies/auth.py`). Users are stored in DB (not hardcoded). Auth endpoints in `app/routes/auth.py`.
- **File Upload**:
  - `POST /books/upload` accepts CSV, schedules background processing (`BackgroundTasks`), and returns an `upload_id`.
  - `GET /books/upload/{upload_id}` reports status from Redis. The processor tracks processed and failed rows internally and surfaces errors; it can be extended to include inserted counts in the status payload if required.
- **Database**:
  - SQLite via `DATABASE_URL` with SQLAlchemy ORM (`app/db/session.py`, `app/db/init_db.py`).
- **Error Handling**:
  - Consistent JSON via `success_response`/`error_response` and Pydantic schema validation for requests/responses.
- **Documentation**:
  - OpenAPI docs available at `/docs` with schemas derived from Pydantic models in `app/schemas/*`.

### Notes

- Make sure Redis is running before starting the API; the app pings Redis on startup.
- Logs are written to `logs/app.log`.
- Default database is SQLite; change `DATABASE_URL` in `.env` to use Postgres/MySQL if desired.
