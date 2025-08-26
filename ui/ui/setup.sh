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

# Function to validate environment variables
validate_env_file() {
    local env_file="$1"
    
    if [ ! -f "$env_file" ]; then
        print_color $RED "Error: $env_file file not found!"
        print_color $YELLOW "Please create a $env_file file based on .env.example before running this script."
        return 1
    fi
    
    print_color $GREEN "✓ $env_file file found"
    
    # Check for required variables
    local required_vars=(
        "NEXT_PUBLIC_WS_OPENFLOW"
        "NEXT_PUBLIC_WS_DEVICESTATS" 
        "NEXT_PUBLIC_WS_CLASIFICATIONS"
        "NEXT_PUBLIC_API_BASE_URL"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$env_file"; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_color $RED "Error: Missing required environment variables in $env_file:"
        for var in "${missing_vars[@]}"; do
            print_color $RED "  - $var"
        done
        return 1
    fi
    
    # Validate API_BASE_URL format
    local api_base_url=$(grep "^NEXT_PUBLIC_API_BASE_URL=" "$env_file" | cut -d'=' -f2-)
    if [[ "$api_base_url" == */ ]]; then
        print_color $RED "Error: NEXT_PUBLIC_API_BASE_URL should NOT end with a trailing slash"
        print_color $YELLOW "Current value: $api_base_url"
        print_color $YELLOW "Please remove the trailing slash and run the script again."
        return 1
    fi
    
    print_color $GREEN "✓ Environment file validation passed"
    return 0
}

# Function to check backend connectivity
check_backend_connectivity() {
    local api_base_url="$1"
    local backend_host=$(echo "$api_base_url" | sed 's|http://||' | sed 's|https://||' | cut -d'/' -f1)
    
    print_color $BLUE "Checking backend connectivity..."
    
    if command_exists curl; then
        if curl -s --connect-timeout 5 --max-time 10 "$api_base_url" >/dev/null 2>&1; then
            print_color $GREEN "✓ Backend is accessible"
            return 0
        else
            print_color $YELLOW "Warning: Cannot reach backend at $api_base_url"
            print_color $YELLOW "Make sure your backend is running before using the frontend."
            return 1
        fi
    elif command_exists wget; then
        if wget -q --timeout=5 --tries=1 "$api_base_url" -O /dev/null 2>/dev/null; then
            print_color $GREEN "✓ Backend is accessible"
            return 0
        else
            print_color $YELLOW "Warning: Cannot reach backend at $api_base_url"
            print_color $YELLOW "Make sure your backend is running before using the frontend."
            return 1
        fi
    else
        print_color $YELLOW "Warning: Cannot test backend connectivity (curl/wget not available)"
        print_color $YELLOW "Make sure your backend is running at $api_base_url"
        return 1
    fi
}

print_header "SDN Launch Control Frontend Setup (TypeScript/Next.js)"

# Check if we're in the correct directory
if [ ! -f "package.json" ] || [ ! -f "next.config.ts" ]; then
    print_color $RED "Error: This doesn't appear to be a Next.js project directory!"
    print_color $RED "Please run this script from the ui/ directory of the sdn-launch-control-ui-ts repository."
    exit 1
fi

# Check for required commands
print_header "Checking Prerequisites"

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

# Validate environment file
print_header "Environment Configuration"

if ! validate_env_file ".env.local"; then
    exit 1
fi

# Display .env.local contents and ask for confirmation
print_color $YELLOW "Current .env.local file contents:"
echo
cat .env.local
echo

read -p "$(print_color $CYAN "Are you happy with these environment settings? (y/N): ")" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_color $YELLOW "Please update your .env.local file and run the script again."
    exit 0
fi

# Check backend connectivity
api_base_url=$(grep "^NEXT_PUBLIC_API_BASE_URL=" .env.local | cut -d'=' -f2-)
check_backend_connectivity "$api_base_url"

# Stop any existing containers
print_header "Stopping Existing Containers"
if docker-compose down 2>/dev/null || docker compose down 2>/dev/null; then
    print_color $GREEN "✓ Stopped any existing containers"
else
    print_color $YELLOW "No existing containers to stop"
fi


# Build the Docker image
print_header "Building Docker Image"
print_color $BLUE "Building the SDN Launch Control frontend image..."
print_color $YELLOW "This may take several minutes as it needs to install Node.js dependencies and build the TypeScript application..."

if docker-compose build --no-cache 2>/dev/null || docker compose build --no-cache 2>/dev/null; then
    print_color $GREEN "✓ Docker image built successfully"
else
    print_color $RED "Error: Failed to build Docker image"
    print_color $YELLOW "This might be a permissions issue. If you're getting permission denied errors,"
    print_color $YELLOW "please check: https://docs.docker.com/engine/install/linux-postinstall/"
    exit 1
fi

# Start the frontend
print_header "Starting Frontend Application"
print_color $BLUE "Starting the Launch Control UI..."

if docker-compose up -d 2>/dev/null || docker compose up -d 2>/dev/null; then
    print_color $GREEN "✓ Frontend application started"
else
    print_color $RED "Error: Failed to start frontend application"
    print_color $YELLOW "Check Docker permissions if you're getting permission denied errors:"
    print_color $YELLOW "https://docs.docker.com/engine/install/linux-postinstall/"
    exit 1
fi

wait_with_countdown 20 "Waiting for frontend application to be ready..."

# Check if frontend is healthy
print_color $BLUE "Checking frontend application health..."
max_attempts=8
attempt=1

while [ $attempt -le $max_attempts ]; do
    # Check health endpoint
    if curl -s http://localhost:3000/api/health >/dev/null 2>&1; then
        print_color $GREEN "✓ Frontend application is healthy and ready"
        break
    fi
    
    # Check container logs for startup indicators
    if docker logs launch-control-ui 2>&1 | grep -q "ready" || \
       docker logs launch-control-ui 2>&1 | grep -q "started server" || \
       docker logs launch-control-ui 2>&1 | grep -q "Local:" || \
       docker logs launch-control-ui 2>&1 | grep -q "Listening on"; then
        print_color $GREEN "✓ Frontend application is ready"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        print_color $YELLOW "Warning: Could not confirm frontend health, but proceeding..."
        print_color $BLUE "You can check the logs with: docker logs launch-control-ui"
        break
    fi
    
    print_color $YELLOW "Attempt $attempt/$max_attempts: Frontend not ready yet, waiting..."
    sleep 5
    ((attempt++))
done

# Final status check
print_header "Deployment Status"
print_color $BLUE "Checking container status..."

if docker-compose ps 2>/dev/null || docker compose ps 2>/dev/null; then
    echo
    print_color $GREEN "✓ Frontend application is running!"
    echo
    print_color $CYAN "You can now access:"
    print_color $YELLOW "- Frontend UI: http://localhost:3000"
    print_color $YELLOW "- Health Check: http://localhost:3000/api/health"
    print_color $YELLOW "- Make sure your backend is running at: $api_base_url"
    echo
    print_color $BLUE "To view logs:"
    print_color $YELLOW "  docker-compose logs -f"
    print_color $YELLOW "  docker logs launch-control-ui"
    echo
    print_color $BLUE "To stop the frontend:"
    print_color $YELLOW "  docker-compose down"
    echo
    print_color $BLUE "Useful commands:"
    print_color $YELLOW "  docker-compose logs           # View application logs"
    print_color $YELLOW "  docker-compose restart        # Restart the application"
    print_color $YELLOW "  docker-compose build --no-cache  # Rebuild without cache"
    print_color $YELLOW "  docker-compose exec launch-control-ui sh  # Access container shell"
    echo
    print_color $BLUE "Container information:"
    print_color $YELLOW "  docker inspect launch-control-ui  # View container details"
    print_color $YELLOW "  docker stats launch-control-ui   # View resource usage"
    echo
else
    print_color $RED "Error: Failed to get container status"
    print_color $YELLOW "This might be a permissions issue. Check:"
    print_color $YELLOW "https://docs.docker.com/engine/install/linux-postinstall/"
    exit 1
fi

print_header "Setup Complete!"
print_color $GREEN "SDN Launch Control frontend is now running successfully!"
print_color $CYAN "Remember to ensure your backend is running for full functionality."
print_color $BLUE "The application is now containerized and ready for production use." 