# Define the virtual environment directory name
VENV_DIR="venv"

echo "Checking for virtual environment..."

# 1. Check if venv exists, if not create it
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv $VENV_DIR
    echo "Venv created."
else
    echo "Virtual environment already exists."
fi

# 2. Activate the virtual environment
source $VENV_DIR/bin/activate

# 3. Install/Update dependencies
echo "Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Create and Run Migrations & Load Seeds
echo "Creating database migrations..."
python manage.py makemigrations

echo "Applying database migrations..."
python manage.py migrate

echo "Loading initial seed data (Brands & Products)..."
if [ -f "licenses/fixtures/seed_data.json" ]; then
    python manage.py loaddata licenses/fixtures/seed_data.json
fi

# 5. Start the development server
echo "Starting Django development server at http://127.0.0.1:8000"
python manage.py runserver
