#!/bin/bash
VENV_DIR="venv"

# Check if the virtual environment directory exists
if [ ! -d "$VENV_DIR" ]; then
    # The virtual environment does not exist, create it
    python3 -m venv "$VENV_DIR" || exit 1

    # Activate the virtual environment
    source "$VENV_DIR/bin/activate" || exit 1

    # Install the requirements
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt || exit 1
    else
        echo "No requirements.txt file found."
        exit 1
    fi
else
    # The virtual environment exists, activate it
    source "$VENV_DIR/bin/activate" || exit 1
    pip3 install -r requirements.txt || exit 1
fi

# Print a message indicating that the virtual environment is activated
echo "Virtual environment activated."

echo "Making migrations"

python3 manage.py makemigrations || exit 1
python3 manage.py migrate || exit 1

echo "Running Redis with docker"
docker compose up -d || exit 1

echo "Populating ClassifierModel if empty"
python3 manage.py initialize_classifier || exit 1
echo "Populating Plugins if empty"
python3 manage.py initialise_plugins || exit 1

echo "Running server"
python3 manage.py runserver 0.0.0.0:8000 || exit 1