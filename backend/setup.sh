#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    printf "${1}${2}${NC}\n"
}

# Function to print section headers
print_header() {
    echo
    print_color $CYAN "=================================="
    print_color $CYAN "$1"
    print_color $CYAN "=================================="
    echo
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait with countdown
wait_with_countdown() {
    local seconds=$1
    local message=$2

    print_color $YELLOW "$message"
    for ((i=seconds; i>0; i--)); do
        printf "\r${YELLOW}Waiting... ${i} seconds remaining${NC}"
        sleep 1
    done
    printf "\r${GREEN}Wait complete!                    ${NC}\n"
}

print_header "SDN Launch Control Backend Setup"

# Check if we're in the correct directory
if [ ! -d "control_center" ]; then
    print_color $RED "Error: control_center directory not found!"
    print_color $RED "Please run this script from the root of the sdn-launch-control-backend repository."
    exit 1
fi

# Check for required commands
print_color $BLUE "Checking prerequisites..."

if ! command_exists docker; then
    print_color $RED "Error: Docker is not installed or not in PATH"
    print_color $YELLOW "Please install Docker first: https://docs.docker.com/engine/install/"
    exit 1
fi

if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    print_color $RED "Error: Docker Compose is not installed or not in PATH"
    print_color $YELLOW "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

print_color $GREEN "✓ Docker and Docker Compose are available"

# Check Docker permissions
print_color $BLUE "Checking Docker permissions..."

if ! docker ps >/dev/null 2>&1; then
    print_color $RED "Error: Cannot run Docker commands without sudo!"
    echo
    print_color $YELLOW "This usually means your user is not in the 'docker' group."
    print_color $YELLOW "To fix this issue, you have two options:"
    echo
    print_color $CYAN "Option 1 (Recommended): Add your user to the docker group"
    print_color $YELLOW "  1. Run: sudo usermod -aG docker \$USER"
    print_color $YELLOW "  2. Log out and log back in (or restart your session)"
    print_color $YELLOW "  3. Verify with: docker ps"
    echo
    print_color $CYAN "Option 2: Run this script with sudo (not recommended for security reasons)"
    print_color $YELLOW "  sudo ./setup.sh"
    echo
    print_color $BLUE "For detailed instructions, see:"
    print_color $BLUE "https://docs.docker.com/engine/install/linux-postinstall/"
    echo
    print_color $RED "Please fix the Docker permissions issue and run this script again."
    exit 1
fi

print_color $GREEN "✓ Docker permissions are correct"

# Test Docker Compose permissions
if ! (docker-compose version >/dev/null 2>&1 || docker compose version >/dev/null 2>&1); then
    print_color $RED "Error: Cannot run Docker Compose commands!"
    print_color $YELLOW "This might be related to Docker permissions. Please ensure Docker is properly configured."
    print_color $BLUE "See: https://docs.docker.com/engine/install/linux-postinstall/"
    exit 1
fi

print_color $GREEN "✓ Docker Compose permissions are correct"

# Change to control_center directory
cd control_center || {
    print_color $RED "Error: Cannot change to control_center directory"
    exit 1
}

print_color $GREEN "✓ Changed to control_center directory"

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_color $RED "Error: .env file not found in control_center directory!"
    print_color $RED "Please create a .env file based on .env.example before running this script."
    print_color $YELLOW "Required variables include:"
    print_color $YELLOW "- CELERY_BROKER_URL"
    print_color $YELLOW "- CHANNEL_REDIS_HOST"
    print_color $YELLOW "- CHANNEL_REDIS_PORT"
    print_color $YELLOW "- DB_HOST, DB_NAME, DB_USER, DB_PASS"
    print_color $YELLOW "- DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD"
    print_color $YELLOW "- TELEGRAM_API_KEY"
    exit 1
fi

print_color $GREEN "✓ .env file found"

# Display .env contents and ask for confirmation
print_header "Environment Configuration"
print_color $YELLOW "Current .env file contents:"
echo
cat .env
echo

read -p "$(print_color $CYAN "Are you happy with these environment settings? (y/N): ")" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_color $YELLOW "Please update your .env file and run the script again."
    exit 0
fi

# Basic validation of .env file
print_color $BLUE "Validating .env file..."

required_vars=("CELERY_BROKER_URL" "DB_HOST" "DB_NAME" "DB_USER" "DB_PASS" "DJANGO_SUPERUSER_USERNAME" "DJANGO_SUPERUSER_EMAIL" "DJANGO_SUPERUSER_PASSWORD")

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env; then
        print_color $RED "Error: Required variable $var not found in .env file"
        exit 1
    fi

    # Check if variable has a value
    value=$(grep "^${var}=" .env | cut -d'=' -f2-)
    if [ -z "$value" ] || [ "$value" = "your_value_here" ] || [ "$value" = "changeme" ]; then
        print_color $RED "Error: Variable $var appears to have a placeholder value. Please set a real value."
        exit 1
    fi
done

print_color $GREEN "✓ .env file validation passed"

# Stop any existing containers
print_header "Stopping Existing Containers"
if docker-compose down 2>/dev/null || docker compose down 2>/dev/null; then
    print_color $GREEN "✓ Stopped any existing containers"
else
    print_color $YELLOW "No existing containers to stop"
fi

# Build the Docker image
print_header "Building Docker Image"
print_color $BLUE "Building the SDN Launch Control backend image..."

if docker-compose build 2>/dev/null || docker compose build 2>/dev/null; then
    print_color $GREEN "✓ Docker image built successfully"
else
    print_color $RED "Error: Failed to build Docker image"
    print_color $YELLOW "This might be a permissions issue. If you're getting permission denied errors,"
    print_color $YELLOW "please check: https://docs.docker.com/engine/install/linux-postinstall/"
    exit 1
fi

# Start database and redis first
print_header "Starting Database and Redis"
print_color $BLUE "Starting PostgreSQL database and Redis..."

if docker-compose up -d pgdatabase redis 2>/dev/null || docker compose up -d pgdatabase redis 2>/dev/null; then
    print_color $GREEN "✓ Database and Redis started"
else
    print_color $RED "Error: Failed to start database and Redis"
    print_color $YELLOW "Check Docker permissions if you're getting permission denied errors:"
    print_color $YELLOW "https://docs.docker.com/engine/install/linux-postinstall/"
    exit 1
fi

wait_with_countdown 10 "Waiting for database and Redis to be ready..."

# Start the Django API
print_header "Starting Django API"
print_color $BLUE "Starting the Launch Control API..."

if docker-compose up -d django 2>/dev/null || docker compose up -d django 2>/dev/null; then
    print_color $GREEN "✓ Django API started"
else
    print_color $RED "Error: Failed to start Django API"
    exit 1
fi

wait_with_countdown 30 "Waiting for Django API to complete migrations and be ready..."

# Check if Django is healthy
print_color $BLUE "Checking Django API health..."
max_attempts=6
attempt=1

while [ $attempt -le $max_attempts ]; do
    if docker logs launch-control-api 2>&1 | grep -q "Application startup complete" || \
       docker logs launch-control-api 2>&1 | grep -q "Uvicorn running"; then
        print_color $GREEN "✓ Django API is healthy and ready"
        break
    fi

    if [ $attempt -eq $max_attempts ]; then
        print_color $YELLOW "Warning: Could not confirm Django API health, but proceeding..."
        print_color $BLUE "You can check the logs with: docker logs launch-control-api"
        break
    fi

    print_color $YELLOW "Attempt $attempt/$max_attempts: Django API not ready yet, waiting..."
    sleep 5
    ((attempt++))
done

# Start Celery worker
print_header "Starting Celery Worker"
print_color $BLUE "Starting Celery worker..."

if docker-compose up -d celery 2>/dev/null || docker compose up -d celery 2>/dev/null; then
    print_color $GREEN "✓ Celery worker started"
else
    print_color $RED "Error: Failed to start Celery worker"
    exit 1
fi

wait_with_countdown 10 "Waiting for Celery worker to be ready..."

# Start Celery beat
print_header "Starting Celery Beat"
print_color $BLUE "Starting Celery beat scheduler..."

if docker-compose up -d celery_beat 2>/dev/null || docker compose up -d celery_beat 2>/dev/null; then
    print_color $GREEN "✓ Celery beat started"
else
    print_color $RED "Error: Failed to start Celery beat"
    exit 1
fi

# Final status check
print_header "Deployment Status"
print_color $BLUE "Checking container status..."

if docker-compose ps 2>/dev/null || docker compose ps 2>/dev/null; then
    echo
    print_color $GREEN "✓ All containers are running!"
    echo
    print_color $CYAN "You can now access:"
    print_color $YELLOW "- Admin Interface: http://localhost:8000/admin"
    print_color $YELLOW "- API Docs: http://localhost:8000/api/docs"
    echo
    print_color $BLUE "To view logs, use:"
    print_color $YELLOW "  docker-compose logs -f [service_name]"
    print_color $YELLOW "  Available services: pgdatabase, redis, django, celery, celery_beat"
    echo
    print_color $BLUE "To stop all services:"
    print_color $YELLOW "  docker-compose down"
    echo
    print_color $BLUE "Useful commands:"
    print_color $YELLOW "  docker-compose logs django     # View Django logs"
    print_color $YELLOW "  docker-compose logs celery     # View Celery worker logs"
    print_color $YELLOW "  docker-compose restart django  # Restart Django service"
    echo
else
    print_color $RED "Error: Failed to get container status"
    print_color $YELLOW "This might be a permissions issue. Check:"
    print_color $YELLOW "https://docs.docker.com/engine/install/linux-postinstall/"
    exit 1
fi

print_header "Setup Complete!"
print_color $GREEN "SDN Launch Control backend is now running successfully!"
