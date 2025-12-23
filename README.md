# Centralized License Service

A multi-tenant license management service for group.one that acts as the single source of truth for all product entitlements across various brands.

## Quick Start

### Docker (Recommended)

```bash
docker-compose up --build
```

That's it! The server will be available at http://localhost:8000

### Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Load seed data
python manage.py loaddata licenses/fixtures/seed_data.json

# Start server
python manage.py runserver
```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/

These provide interactive interfaces where you can browse all endpoints, see request/response schemas, and test the API directly in your browser.

## API Endpoints

- `POST /v1/licenses/provision/` - Provision a license
- `GET /v1/licenses/{key}/status/` - Check license status
- `POST /v1/activations/` - Activate a license seat
- `GET /v1/customers/{email}/licenses/` - List all customer licenses (admin)

## Project Structure

```
centralized-license-service/
├── core/                       # Project-level settings
│   ├── settings.py
│   ├── urls.py                 # Root URL routing
│   └── wsgi.py
├── licenses/                   # The main application
│   ├── migrations/             # Database migration files
│   ├── fixtures/
│   │   └── seed_data.json      # Sample data(Brands and Products)
│   ├── models.py               # Database Schema
│   ├── services.py             # Business Logic (Provisioning/Activation)
│   ├── serializers.py          # DRF Serializers
│   ├── views.py                # API Endpoints
│   ├── urls.py                 # App-level URL routing
│   └── tests.py                # Unit tests for US3 (Seat limits)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt            # django, djangorestframework, psycopg2-binary
├── Explanation.md              # Architecture and design documentation
└── manage.py
```

## Documentation

- **[Explanation.md](Explanation.md)** - Complete architecture and design documentation

## Features

- ✅ Multi-tenant architecture (Brand isolation)
- ✅ License provisioning and activation
- ✅ Seat limit enforcement
- ✅ Status checking
- ✅ Ecosystem-wide license view
- ✅ Interactive API documentation (Swagger/ReDoc)
- ✅ Docker support
- ✅ PostgreSQL database

## Requirements

- Python 3.9+
- PostgreSQL 14+
- Docker (optional, for containerized setup)

## License

This project was created by **Godfrey Samuel** (<godfreysam09@gmail.com>) as part of a coding exercise.


