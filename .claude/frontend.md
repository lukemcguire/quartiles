# Frontend Architecture

## Directory Structure

```
frontend/src/
├── main.tsx              # App entry point, sets up TanStack Router/Query, theme provider
├── routes/               # File-based routing with TanStack Router
│   ├── __root.tsx        # Root layout
│   ├── _layout.tsx       # Authenticated layout with sidebar
│   ├── login.tsx         # Public routes
│   ├── signup.tsx
│   └── _layout/          # Protected routes (require auth)
│       ├── index.tsx
│       └── items.tsx
├── client/               # Auto-generated TypeScript API client (DO NOT EDIT)
├── components/           # React components by feature
└── hooks/                # Custom React hooks
```

## Routing

- Uses **TanStack Router** with file-based routing
- Routes under `_layout/` require authentication
- 401/403 responses trigger logout and redirect to login (handled in main.tsx)

## State Management

- **TanStack Query** for server state
- API client configured with `OpenAPI.BASE` and `OpenAPI.TOKEN` in main.tsx
- JWT token stored in localStorage

## Styling

- **Tailwind CSS** for styling
- **shadcn/ui** components (Tailwind-based)
- Dark mode supported via theme-provider

## Frontend Commands

```bash
cd frontend && npm install  # Install dependencies
make frontend-dev           # Start dev server (Vite at localhost:5173)
make frontend-build         # Build for production
make frontend-lint          # Run ESLint
```

## API Client

The TypeScript client in `frontend/src/client/` is **auto-generated** from the OpenAPI schema.

**Critical:** Never edit manually. Regenerate after modifying backend API routes:

```bash
make generate-client
```
