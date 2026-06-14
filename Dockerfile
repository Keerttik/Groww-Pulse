# Stage 1: Build the Vite frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/web
COPY web/package.json web/package-lock.json* ./
RUN npm install
COPY web/ ./
RUN npm run build

# Stage 2: Build the Python backend
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc sqlite3 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir uvicorn

# Copy the Python backend
COPY agent/ ./agent/
COPY play_store_mcp/ ./play_store_mcp/
COPY config.json mcp_servers.json ./

# Copy the compiled frontend from Stage 1
COPY --from=frontend-builder /app/web/dist ./web/dist

# Expose port
EXPOSE 8000

# Run the FastAPI server
CMD ["python", "-m", "uvicorn", "agent.api:app", "--host", "0.0.0.0", "--port", "8000"]
