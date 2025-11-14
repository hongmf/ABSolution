# ABSolution Frontend

Modern React + TypeScript frontend for the ABSolution ABS Analytics Platform.

## Features

- **Data Panel**: Interactive table for viewing SEC filing data
- **Real-time Filtering**: Filter by issuer, asset class, date range, and risk scores
- **Sortable Columns**: Click any column header to sort data
- **Metrics Dashboard**: Key performance indicators at a glance
- **Data Visualization**: Charts showing trends and distributions
- **Responsive Design**: Works on desktop and mobile devices

## Technology Stack

- **React 18**: Modern React with hooks
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and dev server
- **Recharts**: Data visualization library
- **Axios**: HTTP client for API calls
- **date-fns**: Date formatting utilities

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
# Install dependencies
npm install

# Or from the root directory
npm run frontend:install
```

### Development

```bash
# Start development server
npm run dev

# Or from the root directory
npm run frontend:dev
```

The development server will start at `http://localhost:3000`.

### Build

```bash
# Build for production
npm run build

# Or from the root directory
npm run frontend:build
```

The production build will be created in the `dist` directory.

### Preview Production Build

```bash
# Preview production build locally
npm run preview

# Or from the root directory
npm run frontend:preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts           # API client for backend communication
│   ├── components/
│   │   ├── DataPanel.tsx       # Main data panel component
│   │   ├── FilingTable.tsx     # Sortable filing table
│   │   ├── MetricsCard.tsx     # Metrics display
│   │   ├── FilterPanel.tsx     # Data filtering controls
│   │   ├── DataVisualization.tsx  # Charts and graphs
│   │   ├── ErrorMessage.tsx    # Error display
│   │   └── LoadingSpinner.tsx  # Loading indicator
│   ├── types/
│   │   └── index.ts            # TypeScript type definitions
│   ├── App.tsx                 # Root application component
│   ├── App.css                 # Application styles
│   ├── main.tsx                # Application entry point
│   └── index.css               # Global styles
├── index.html                  # HTML template
├── vite.config.ts              # Vite configuration
├── tsconfig.json               # TypeScript configuration
├── package.json                # Dependencies and scripts
└── README.md                   # This file
```

## API Integration

The frontend connects to the backend API via the API client in `src/api/client.ts`. By default, it proxies requests to `http://localhost:8000/api`.

To change the API endpoint, update the proxy configuration in `vite.config.ts`.

## Available API Endpoints

- `GET /api/filings` - Fetch filing data
- `GET /api/benchmark` - Get issuer benchmarks
- `GET /api/issuers` - List all issuers
- `GET /api/asset-classes` - List all asset classes

## Error Handling

The Data panel includes comprehensive error handling:

- Network errors are caught and displayed to users
- Failed API calls show retry buttons
- Loading states prevent multiple simultaneous requests
- TypeScript ensures type safety throughout

## Performance Optimization

- Client-side filtering for risk scores
- Virtualization-ready table structure
- Lazy loading of chart library
- Production builds are minified and optimized

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

MIT
