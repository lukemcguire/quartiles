# Frontend Dockerfile
# Multi-stage build: bun workspace build + nginx serve

# Install bun in all stages
FROM oven/bun:1-alpine AS bun-base

# Development stage
FROM bun-base AS development

WORKDIR /app

# Copy workspace files (root package.json and bun.lock)
COPY package.json bun.lock ./
COPY frontend/package.json ./frontend/

# Install dependencies using bun workspace
RUN bun install

# Copy frontend source code
COPY frontend/ ./frontend/

WORKDIR /app/frontend

# Expose Vite dev server port
EXPOSE 5173

# Development command
CMD ["bun", "run", "dev", "--", "--host", "0.0.0.0"]


# Build stage
FROM bun-base AS builder

WORKDIR /app

# Copy workspace files (root package.json and bun.lock)
COPY package.json bun.lock ./
COPY frontend/package.json ./frontend/

# Install dependencies using bun workspace
RUN bun install

# Copy frontend source code
COPY frontend/ ./frontend/

WORKDIR /app/frontend

# Build argument for API URL
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# Build the application
RUN bun run build


# Production stage
FROM nginx:alpine AS production

# Copy nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend/nginx-backend-not-found.conf /etc/nginx/extra-conf.d/backend-not-found.conf

# Copy built assets from builder stage
COPY --from=builder /app/frontend/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
