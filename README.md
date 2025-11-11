# SDN Launch Control

A comprehensive Software-Defined Networking (SDN) management platform that enables easy and automated adoption of the SDN paradigm into new or pre-existing networks. This monorepo contains both the backend API and frontend.

For detailed documentation consult our [website](https://taurine-technology.github.io/).

## 🚀 Quick Start

### Prerequisites

Successfully Tested on Ubuntu Desktop, Ubuntu Server, Windows WSL and Mac.

Requires:

- Docker and Docker Compose

### Backend Setup

1. From the root of the repo **Navigate to the backend directory:**

   ```bash
   cd backend/control_center
   ```

2. **Create environment configuration:**

   ```bash
   cp .env.example control_center/.env
   # Edit .env with your configuration
   ```

3. **Start the docker containers:**

   ```bash
   docker compose up -d
   ```

### Frontend Setup

1. From the root of the repo **Navigate to the UI directory:**

   ```bash
   cd ui/ui/
   ```

2. **Create environment configuration:**

   ```bash
   cp .example .env.local
   # Edit .env.local with your backend API URLs
   ```

3. **Install dependencies and start:**

   ```bash
   ./setup.sh
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000 / http://<SERVER_IP_ADDRESS>:3000
   - Backend API: http://localhost:8000 / http://<SERVER_IP_ADDRESS>:8000
   - Admin Interface: http://localhost:8000/admin / http://<SERVER_IP_ADDRESS>:8000/admin

## 🔧 Development

### Backend Development

```bash
cd backend/control_center/
docker compose -f docker-compose.dev.yml up
```

### Frontend Development

```bash
cd ui/ui/
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

### Environment Variables

#### Backend (.env)

To generate a secret key use the following:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

```env
# Celery
CELERY_BROKER_URL=redis://redis:6379/1

# Channels (Redis for WebSockets)
CHANNEL_REDIS_HOST=redis
CHANNEL_REDIS_PORT=6379

# Database
DB_HOST=pgdatabase
DB_NAME=postgres
DB_USER=postgres
DB_PASS=postgres
DB_PORT=5432

# Database Connection Pool Settings (Production)
DB_MAX_CONNS=20
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=3600

# Database Connection Pool Settings (Development)
DB_MAX_CONNS_DEV=10
DB_MAX_OVERFLOW_DEV=5

# Default User Login
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin

# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_LOG_LEVEL=INFO

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000
CORS_ORIGIN_ALLOW_ALL=False

# Telegram
TELEGRAM_API_KEY=your-telegram-api-key-here

# Docker Image (for docker-compose.yml production)
# Set this to the published Docker Hub image you want to use
# Example: taurinetech/sdn-launch-control-backend:latest
# DOCKER_IMAGE=taurinetech/sdn-launch-control-backend
```

#### Frontend (.env.local)

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_OPENFLOW=ws://localhost:8000/ws/openflow_metrics/
NEXT_PUBLIC_WS_DEVICESTATS=ws://localhost:8000/ws/device_stats/
NEXT_PUBLIC_WS_CLASIFICATIONS=ws://localhost:8000/ws/flow_updates/
```

## 🤝 Contributing

Please keep your contributions focused and small to help with pull request management.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run linting and integration tests
5. Submit a pull request

## 📄 License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

> **⚠️ Warning**: Closed-source commercial usage is not permitted with the GPL-3.0 license. If this license is not compatible with your use case, please contact keeganwhite@taurinetech.com to purchase a commercial license.

## 🆘 Support

For issues, questions, or commercial licensing:

- **Email**: keeganwhite@taurinetech.com
- **Contributor License Agreement**: [CLA](https://gist.github.com/keeganwhite/b41ddb8a761ccd6e6498a5cad4eb4d9b)

## 🎥 Video Content

Watch the v1.0.0 release installation guide [here](https://youtu.be/BMdbTTLqWG0?si=BHCsDOqXWhxoyXjQ)

[_DEPRECIATED_] Watch the [pre-production alpha release installation guide](https://youtu.be/eFjDr7ym5Yw) to see SDN Launch Control in action.

---
