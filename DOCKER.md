# Docker Setup Guide

Complete guide for running the Grocery List app with Docker.

## Quick Start

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your Supabase credentials (see below)
nano .env  # or use your preferred editor

# 3. Start services
docker-compose up -d

# 4. View logs
docker-compose logs -f

# 5. Access the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Environment Variables

### Required Supabase Credentials

You need these from your Supabase project:

1. **Go to** https://supabase.com → Create/Select Project
2. **Navigate to** Settings → API
3. **Copy these values to your `.env` file:**

```bash
# Backend - Uses service key (has admin privileges)
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGci...  # Service role key (secret)

# Frontend - Uses anon key (safe to expose)
VITE_SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGci...  # Anon public key
```

**Important:** The `SUPABASE_KEY` for backend is the **service_role** key, NOT the anon key.

## Docker Compose Configurations

### Production Mode (docker-compose.yaml)

Optimized builds, no hot-reload:
```bash
docker-compose up -d
```

**Features:**
- Multi-stage builds (smaller images)
- Frontend served via nginx
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

### Development Mode (docker-compose.dev.yaml)

Hot-reload enabled for both services:
```bash
docker-compose -f docker-compose.dev.yaml up
```

**Features:**
- Code changes auto-reload
- Volume mounts for live editing
- Vite dev server with HMR
- Frontend: http://localhost:5173
- Backend: http://localhost:8000

## Docker Commands

### Starting Services
```bash
# Production mode (detached)
docker-compose up -d

# Development mode (watch logs)
docker-compose -f docker-compose.dev.yaml up

# Rebuild and start
docker-compose up -d --build
```

### Viewing Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

### Stopping Services
```bash
# Stop containers (keep data)
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove everything including volumes
docker-compose down -v
```

### Rebuilding
```bash
# Rebuild specific service
docker-compose build backend
docker-compose build frontend

# Rebuild all
docker-compose build

# Force rebuild (no cache)
docker-compose build --no-cache
```

### Accessing Containers
```bash
# Execute command in running container
docker-compose exec backend bash
docker-compose exec frontend sh

# Run one-off command
docker-compose run backend python -m spacy download en_core_web_sm
```

## Architecture

### Services

**Backend (Python/FastAPI)**
- Port: 8000
- Base image: python:3.11-slim
- Includes: Tesseract OCR, spaCy
- Health check: GET /health

**Frontend (React/Vite)**
- Port: 3000 (prod) / 5173 (dev)
- Production: nginx serving static build
- Development: Vite dev server with HMR

### Networking
- All services on custom network: `grocery-list-network`
- Services communicate by service name (e.g., `http://backend:8000`)

### Volumes

**Development mode only:**
```yaml
backend:
  volumes:
    - ./backend:/app           # Code sync
    - /app/__pycache__         # Exclude cache

frontend:
  volumes:
    - ./frontend:/app          # Code sync
    - /app/node_modules        # Exclude node_modules
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port
sudo lsof -i :8000
sudo lsof -i :3000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yaml
ports:
  - "8001:8000"  # Map to different host port
```

### Supabase Connection Failed
```bash
# Check environment variables are loaded
docker-compose exec backend env | grep SUPABASE

# Test connection
docker-compose exec backend python -c "
import os
from supabase import create_client
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
print('Connection successful')
"
```

### Backend Health Check Failing
```bash
# Check backend logs
docker-compose logs backend

# Test health endpoint
curl http://localhost:8000/health

# Check if uvicorn started
docker-compose exec backend ps aux | grep uvicorn
```

### Frontend Not Loading
```bash
# Check nginx is running (production)
docker-compose exec frontend ps aux | grep nginx

# Check if build succeeded
docker-compose logs frontend | grep -i error

# Test directly
curl http://localhost:3000
```

### Tesseract OCR Not Found
```bash
# Verify Tesseract installed in backend container
docker-compose exec backend tesseract --version

# If missing, rebuild:
docker-compose build --no-cache backend
```

### spaCy Model Not Found
```bash
# Download model manually
docker-compose exec backend python -m spacy download en_core_web_sm

# Or rebuild (model downloaded during build)
docker-compose build backend
```

### Docker Build Fails - Disk Space
```bash
# Clean up Docker
docker system prune -a
docker volume prune

# Check disk space
df -h
```

### Changes Not Reflecting (Dev Mode)
```bash
# Ensure using dev compose file
docker-compose -f docker-compose.dev.yaml up

# Check volumes mounted correctly
docker-compose -f docker-compose.dev.yaml ps
docker inspect <container_id> | grep Mounts -A 10

# Restart services
docker-compose -f docker-compose.dev.yaml restart
```

### CORS Errors in Frontend
```bash
# Check backend ALLOWED_ORIGINS includes frontend URL
docker-compose exec backend env | grep ALLOWED_ORIGINS

# Should include: http://localhost:3000,http://localhost:5173

# Update in .env then restart:
docker-compose restart backend
```

## Production Deployment

### Building for Production
```bash
# Build optimized images
docker-compose build

# Tag images
docker tag grocery-list-backend:latest your-registry/grocery-list-backend:v1.0.0
docker tag grocery-list-frontend:latest your-registry/grocery-list-frontend:v1.0.0

# Push to registry
docker push your-registry/grocery-list-backend:v1.0.0
docker push your-registry/grocery-list-frontend:v1.0.0
```

### Deployment Platforms

**DigitalOcean App Platform:**
```bash
# Use docker-compose.yaml
# Set environment variables in dashboard
# Connect GitHub repo for auto-deploy
```

**AWS ECS:**
```bash
# Create task definitions from docker-compose
# Use AWS ECR for images
# Configure load balancer for frontend
```

**Railway.app:**
```bash
# Connect GitHub repo
# Railway auto-detects Dockerfile
# Set environment variables in dashboard
```

## Security Best Practices

1. **Never commit `.env` files**
   ```bash
   # Verify .env is gitignored
   cat .gitignore | grep .env
   ```

2. **Use secrets in production**
   ```bash
   # Docker secrets or platform-specific secret management
   # Never expose SUPABASE_KEY (service role key)
   ```

3. **Update base images regularly**
   ```dockerfile
   # Pin specific versions
   FROM python:3.11-slim
   # Not just: FROM python
   ```

4. **Scan for vulnerabilities**
   ```bash
   docker scan grocery-list-backend
   docker scan grocery-list-frontend
   ```

## Performance Tips

1. **Use multi-stage builds** (already implemented)
   - Smaller final images
   - Faster deployments

2. **Optimize layer caching**
   - Copy requirements first
   - Copy code last
   - Only invalidates changed layers

3. **Use .dockerignore** (already implemented)
   - Reduces build context size
   - Faster builds

4. **Enable BuildKit**
   ```bash
   export DOCKER_BUILDKIT=1
   docker-compose build
   ```

## Monitoring

### Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Frontend health (production)
curl http://localhost:3000

# Check health status in Docker
docker-compose ps
# Healthy services show: Up (healthy)
```

### Resource Usage
```bash
# View resource consumption
docker stats

# View specific container
docker stats grocery-list-backend-1
```

## Backup & Restore

### Backup Volumes (if using local databases)
```bash
# Backup
docker run --rm --volumes-from grocery-list-backend-1 \
  -v $(pwd):/backup alpine tar czf /backup/backend-backup.tar.gz /app

# Restore
docker run --rm --volumes-from grocery-list-backend-1 \
  -v $(pwd):/backup alpine tar xzf /backup/backend-backup.tar.gz
```

**Note:** This app uses Supabase (external), so backups are handled by Supabase.

## Development Workflow

### Recommended Process

1. **Start dev mode**
   ```bash
   docker-compose -f docker-compose.dev.yaml up
   ```

2. **Make code changes**
   - Edit files locally
   - Changes auto-reload in containers

3. **Test changes**
   ```bash
   # Backend tests (when implemented)
   docker-compose exec backend pytest

   # Frontend tests (when implemented)
   docker-compose exec frontend npm test
   ```

4. **Check logs**
   ```bash
   docker-compose logs -f backend
   ```

5. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push
   ```

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Supabase Documentation](https://supabase.com/docs)
- [FastAPI Docker Documentation](https://fastapi.tiangolo.com/deployment/docker/)
- [Vite Docker Guide](https://vitejs.dev/guide/build.html)
