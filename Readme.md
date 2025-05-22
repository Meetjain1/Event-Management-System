# Collaborative Event Management System

A RESTful API for managing events with collaborative editing features, version control, and real-time updates.

## Features

- User authentication with JWT tokens
- Role-based access control (Owner, Editor, Viewer)
- Event management with CRUD operations
- Recurring events support
- Version control with changelog and diff visualization
- Collaborative editing with granular permissions
- Real-time notifications for changes
- Comprehensive API documentation

## Tech Stack

- FastAPI - Modern, fast web framework for building APIs
- PostgreSQL - Robust relational database
- SQLAlchemy - SQL toolkit and ORM
- Alembic - Database migration tool
- Redis - For rate limiting and caching
- Pydantic - Data validation using Python type annotations
- JWT - For secure authentication

Event Management System API

1. API Documentation: https://event-management-system-9gy4.onrender.com/docs
   - Interactive Swagger documentation
   - Test all API endpoints
   - View request/response schemas

2. Base API URL: https://event-management-system-9gy4.onrender.com
   Main endpoints:
   - /api/auth/* - Authentication endpoints
   - /api/events/* - Event management endpoints
   
Note: The base URL will show "Not Found" because it's an API server, not a website. 
Please use the Swagger documentation (/docs) to explore and test the API.

## Prerequisites

- Python 3.8+
- PostgreSQL
- Redis

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd event_management_system
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory:
```env
# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=event_management

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_URL=redis://localhost
```

5. Initialize the database:
```bash
alembic upgrade head
```

6. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

### Authentication Endpoints

#### Register a new user
```http
POST /api/auth/register
Content-Type: application/json

{
    "username": "string",
    "email": "user@example.com",
    "password": "string",
    "full_name": "string"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=string&password=string
```

#### Refresh token
```http
POST /api/auth/refresh
Authorization: Bearer <refresh_token>
```

#### Logout
```http
POST /api/auth/logout
Authorization: Bearer <access_token>
```

### Event Management Endpoints

#### Create an event
```http
POST /api/events
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "title": "string",
    "description": "string",
    "start_time": "2024-03-15T14:30:00Z",
    "end_time": "2024-03-15T16:30:00Z",
    "location": "string",
    "is_recurring": false,
    "recurrence_pattern": {
        "frequency": "WEEKLY",
        "interval": 1,
        "until": "2024-12-31T00:00:00Z"
    }
}
```

#### List events
```http
GET /api/events?skip=0&limit=100&start_date=2024-03-15T00:00:00Z&end_date=2024-03-16T00:00:00Z
Authorization: Bearer <access_token>
```

#### Get event by ID
```http
GET /api/events/{id}
Authorization: Bearer <access_token>
```

#### Update event
```http
PUT /api/events/{id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "title": "Updated Title",
    "description": "Updated description"
}
```

#### Delete event
```http
DELETE /api/events/{id}
Authorization: Bearer <access_token>
```

### Collaboration Endpoints

#### Share event
```http
POST /api/events/{id}/share
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "user_id": 0,
    "role": "EDITOR"
}
```

#### Get event version
```http
GET /api/events/{id}/history/{version_id}
Authorization: Bearer <access_token>
```

#### Get changelog
```http
GET /api/events/{id}/changelog
Authorization: Bearer <access_token>
```

#### Get version diff
```http
GET /api/events/{id}/diff/{version_id1}/{version_id2}
Authorization: Bearer <access_token>
```

## Error Handling

The API uses standard HTTP status codes:

- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Validation Error
- 500: Internal Server Error

## Rate Limiting

The API implements rate limiting to prevent abuse:

- 60 requests per minute per IP address
- Rate limit headers are included in the response

## Testing

Run the tests using pytest:
```bash
pytest
```

## License

MIT # Event-Management-System
