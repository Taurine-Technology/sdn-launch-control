# SDN Launch Control

A comprehensive Software-Defined Networking (SDN) management platform that enables easy and automated adoption of the SDN paradigm into new or pre-existing networks. This monorepo contains both the backend API and modern TypeScript React frontend.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Tested on Ubuntu Desktop, Ubuntu Server, Windows WSL and Mac.

### Backend Setup

1. **Navigate to the backend directory:**

   ```bash
   cd backend/
   ```

2. **Create environment configuration:**

   ```bash
   cp control_center/.env.example control_center/.env
   # Edit .env with your configuration
   ```

3. **Run the automated setup:**

   ```bash
   ./setup.sh
   ```

### Frontend Setup

1. **Navigate to the UI directory:**

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
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Admin Interface: http://localhost:8000/admin

## 📁 Project Structure

```
sdn-launch-control/
├── backend/                    # Django REST API backend
│   ├── control_center/         # Main Django application
│   │   ├── account/           # User authentication & profiles
│   │   ├── ansible/           # Ansible playbooks & automation
│   │   ├── classifier/        # ML traffic classification
│   │   ├── controller/        # SDN controller management
│   │   ├── device_monitoring/ # Real-time device monitoring
│   │   ├── network_data/      # Network analytics & data
│   │   ├── network_device/    # Device management
│   │   ├── notification/      # Telegram notifications
│   │   ├── odl/              # OpenDaylight integration
│   │   ├── onos/             # ONOS integration
│   │   ├── ovs_install/      # Open vSwitch installation
│   │   ├── software_plugin/  # Plugin system
│   │   └── utils/            # Utility functions
│   ├── setup.sh              # Backend setup script
│   └── README.md             # Backend documentation
├── ui/                        # Next.js React frontend
│   ├── src/
│   │   ├── app/              # Next.js app router pages
│   │   ├── components/       # React components
│   │   ├── context/          # React context providers
│   │   ├── hooks/            # Custom React hooks
│   │   ├── lib/              # Utility functions & API calls
│   │   └── locales/          # Internationalization files
│   ├── public/               # Static assets
│   ├── Dockerfile            # Frontend containerization
│   ├── docker-compose.yml    # Frontend services
│   └── README.md             # Frontend documentation
└── README.md                 # This file
```

## 🎯 Features

### Backend Features

- **Device Management**: Automated installation and configuration of Open vSwitch
- **Controller Integration**: Support for OpenDaylight controllers
- **Traffic Classification**: Machine learning-based traffic analysis and categorization
- **Network Monitoring**: Real-time device statistics and performance metrics
- **Plugin System**: Extensible architecture for custom network functionality
- **Automation**: Ansible-based deployment and configuration management
- **Notifications**: Telegram integration for alerts and reports
- **REST API**: Comprehensive API for frontend integration

### Frontend Features

- **Modern UI**: Built with React, TypeScript, and Next.js
- **Device Management**: Intuitive interface for switches and controllers
- **Real-time Monitoring**: Live charts and statistics using WebSocket connections
- **Network Visualization**: Interactive network topology diagrams
- **Plugin Management**: Install and configure network plugins
- **Multi-language Support**: Internationalization (English/Spanish)
- **Responsive Design**: interface designed with shadcn components

## 🛠 Technology Stack

### Backend

- **Framework**: Django with Django REST Framework
- **Database**: PostgreSQL with TimescaleDB for time-series data
- **Message Broker**: Redis with Celery for background tasks
- **WebSockets**: Django Channels for real-time communication
- **ML/AI**: TensorFlow/Keras for traffic classification
- **Automation**: Ansible for infrastructure management
- **Containerization**: Docker & Docker Compose

### Frontend

- **Framework**: Next.js with React
- **Language**: TypeScript for type safety
- **Styling**: Tailwind CSS with shadcn/ui components
- **State Management**: React Context API
- **HTTP Client**: Axios for API communication
- **Charts**: Recharts for data visualization
- **Icons**: Lucide React
- **Forms**: React Hook Form with Zod validation

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

```env
# Database
DB_HOST=pgdatabase
DB_NAME=postgres
DB_USER=postgres
DB_PASS=postgres
DB_PORT=5432

# Redis
CELERY_BROKER_URL=redis://redis:6379/1
CHANNEL_REDIS_HOST=redis
CHANNEL_REDIS_PORT=6379

# Django
DEBUG=False
DJANGO_LOG_LEVEL=INFO
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=admin

# Telegram
TELEGRAM_API_KEY=your_telegram_api_key
```

#### Frontend (.env.local)

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_OPENFLOW=ws://localhost:8000/ws/openflow_metrics/
NEXT_PUBLIC_WS_DEVICESTATS=ws://localhost:8000/ws/device_stats/
NEXT_PUBLIC_WS_CLASIFICATIONS=ws://localhost:8000/ws/flow_updates/
```

## 🐳 Docker Deployment

### Backend

```bash
cd backend/control_center/
docker-compose up -d
```

### Frontend

```bash
cd ui/
docker-compose up -d
```

## 📚 Documentation

- **Backend Architecture**: [backend/control_center/docs/](backend/control_center/docs/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run linting and tests
5. Submit a pull request

### Development Guidelines

- Follow TypeScript best practices for frontend code
- Use Django coding standards for backend code
- Write comprehensive tests for new features
- Update documentation for API changes

## 📄 License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

> **⚠️ Warning**: Closed-source commercial usage is not permitted with the GPL-3.0 license. If this license is not compatible with your use case, please contact keeganwhite@taurinetech.com to purchase a commercial license.

## 🆘 Support

For issues, questions, or commercial licensing:

- **Email**: keeganwhite@taurinetech.com
- **Contributor License Agreement**: [CLA](https://gist.github.com/keeganwhite/b41ddb8a761ccd6e6498a5cad4eb4d9b)

## 🎥 Demo

New demo video coming soon!

[_DEPRECIATED_] Watch the [pre-production alpha release demo](https://youtu.be/eFjDr7ym5Yw) to see SDN Launch Control in action.

---

**SDN Launch Control** - Empowering network automation and management through modern SDN technologies.
