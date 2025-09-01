# Unpuzzle MVP

A full-stack learning platform with course management, AI assistance, and analytics.

## Prerequisites

- Node.js 20+ and pnpm 10+
- Python 3.8+
- Django

## Setup

### 1. Install Dependencies

```bash
pnpm install
```

### 2. Backend Setup

```bash
pnpm run backend:setup
```

This will:
- Create Python virtual environment
- Install Python dependencies
- Set up Django database
- Create superuser (follow prompts)

### 3. Start Development
### Individual Services

```bash
# Frontend only
pnpm run frontend:dev

# Backend only  
pnpm run backend:dev
```

## Scripts

- `pnpm run dev` - Start both frontend and backend
- `pnpm run build` - Build all packages
- `pnpm run lint` - Lint all packages
- `pnpm run backend:setup` - Setup backend environment

## Architecture

- **Frontend**: Next.js with TypeScript and Tailwind CSS
- **Backend**: Django REST API with SQLite
- **Monorepo**: pnpm workspaces with shared packages

## URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:3001