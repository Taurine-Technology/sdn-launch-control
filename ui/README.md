# SDN Launch Control UI

A modern TypeScript React application for managing Software-Defined Networking (SDN) infrastructure with a focus on OpenFlow controllers, switches, and network monitoring.

## Features

- **Device Management**: Add, configure, and manage switches and controllers
- **Network Monitoring**: Real-time traffic classification and data usage analytics
- **Plugin System**: Extensible plugin architecture for network functionality
- **Multi-language Support**: Internationalization with English and Spanish
- **Modern UI**: Built with React, TypeScript, and shadcn/ui components

## Run the code (source)

1. Create a `.env.local` file in the root repo using the variables in [.example](./sdn-launch-control/.example).
2. Install dependencies `npm install`.
3. Run the code `npm run dev`.

## Development

### Project Structure

```
sdn-launch-control-ui-ts/
├── ui/                          # Frontend application
│   ├── src/
│   │   ├── app/                # Next.js app router pages
│   │   ├── components/         # React components
│   │   ├── lib/               # Utility functions and API calls
│   │   ├── context/           # React context providers
│   │   └── locales/           # Translation files
│   └── public/                # Static assets
└── README.md                  # This file
```

### Key Technologies

- **Frontend**: React 18, TypeScript, Next.js 14
- **UI Components**: shadcn/ui, Tailwind CSS
- **State Management**: React Context API
- **HTTP Client**: Axios
- **Notifications**: Sonner
- **Charts**: Recharts
- **Icons**: Lucide React

### Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript type checking
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run linting and type checking
5. Submit a pull request

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

## Support

For issues and questions, please contact Keegan White at keeganwhite@taurinetech.com.
