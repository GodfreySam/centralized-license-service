#!/bin/bash
set -e

echo "🚀 Starting License Service..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for database to be ready..."
until python manage.py shell -c "from django.db import connection; connection.ensure_connection()" 2>/dev/null; do
  echo "   Database is unavailable - sleeping"
  sleep 1
done
echo "✅ Database is ready!"

# Create migrations if they don't exist
echo "📝 Checking for migrations..."
if [ ! -d "licenses/migrations" ] || [ -z "$(ls -A licenses/migrations/*.py 2>/dev/null | grep -v __init__)" ]; then
  echo "   Creating initial migrations..."
  python manage.py makemigrations licenses || echo "   No new migrations needed"
else
  echo "   Migrations already exist"
fi

# Apply migrations
echo "🔄 Applying database migrations..."
python manage.py migrate --noinput

# Load seed data (idempotent - safe to run multiple times)
echo "🌱 Loading seed data..."
if python manage.py loaddata licenses/fixtures/seed_data.json 2>/dev/null; then
  echo "   ✅ Seed data loaded"
else
  echo "   ⚠️  Seed data already exists or file not found (this is okay)"
fi

# Collect static files (if needed in future)
# python manage.py collectstatic --noinput

echo "✅ Setup complete! Starting server..."
exec "$@"
