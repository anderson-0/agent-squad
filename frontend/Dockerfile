# Development Dockerfile for Frontend (Next.js with Bun)
FROM oven/bun:1-alpine

WORKDIR /app

# Install system dependencies for native modules
RUN apk add --no-cache libc6-compat

# Copy dependency files
COPY frontend/package.json frontend/bun.lock* ./

# Install dependencies
RUN bun install --frozen-lockfile

# Copy application code
COPY frontend/ .

# Expose port
EXPOSE 3000

# Set environment
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD wget --spider -q http://localhost:3000 || exit 1

# Start development server
CMD ["bun", "run", "dev"]
