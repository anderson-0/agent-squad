# Development Dockerfile for Frontend with Bun
FROM oven/bun:1.1.38-alpine

WORKDIR /app

# Copy dependency files
COPY frontend/package.json frontend/bun.lock* ./

# Install dependencies with Bun
RUN bun install --frozen-lockfile

# Copy application code
COPY frontend/ .

# Create non-root user for security
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD wget --spider -q http://localhost:3000 || exit 1

# Start development server with Bun
CMD ["bun", "run", "dev"]
