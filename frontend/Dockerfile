# Frontend Dockerfile
# Multi-stage build: npm build + nginx serve

# Development stage
FROM node:20-alpine AS development

WORKDIR /app/frontend

# Copy package files (only frontend files, not root workspace package.json)
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy frontend source code
COPY frontend/ ./

# Expose Vite dev server port
EXPOSE 5173

# Development command
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


# Build stage
FROM node:20-alpine AS builder

WORKDIR /app/frontend

# Copy package files (only frontend files, not root workspace package.json)
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy frontend source code
COPY frontend/ ./

# Build argument for API URL
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# Build the application
RUN npm run build


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
