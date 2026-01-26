# GenGlossary Frontend

React + TypeScript frontend for GenGlossary.

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Package Manager**: pnpm
- **UI Library**: Mantine v7
- **Routing**: TanStack Router
- **Data Fetching**: TanStack Query
- **Testing**: Vitest + React Testing Library + MSW

## Development

### Install dependencies

```bash
pnpm install
```

### Start development server

```bash
pnpm dev
```

The frontend runs at http://localhost:5173

### Run tests

```bash
# Run tests once
pnpm test

# Run tests in watch mode
pnpm test:watch
```

### Lint code

```bash
pnpm lint
```

### Build for production

```bash
pnpm build
```

## Project Structure

```
frontend/
├── src/
│   ├── __tests__/          # Test files
│   │   ├── setup.ts        # Test setup (MSW, mocks)
│   │   ├── app-shell.test.tsx
│   │   ├── routing.test.tsx
│   │   └── api-client.test.ts
│   ├── api/
│   │   ├── client.ts       # API client
│   │   ├── types.ts        # API types
│   │   └── hooks/          # TanStack Query hooks
│   ├── components/
│   │   ├── common/         # Shared components
│   │   └── layout/         # Layout components
│   │       ├── AppShell.tsx
│   │       ├── GlobalTopBar.tsx
│   │       ├── LeftNavRail.tsx
│   │       └── LogPanel.tsx
│   ├── routes/             # TanStack Router routes
│   ├── theme/              # Mantine theme
│   └── main.tsx            # Entry point
├── .env                    # Environment variables
├── .env.example            # Environment template
├── vitest.config.ts        # Vitest configuration
└── vite.config.ts          # Vite configuration
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` |

## Running with Backend

```bash
# Terminal 1: Start backend
uv run genglossary api serve --reload

# Terminal 2: Start frontend
cd frontend && pnpm dev
```
