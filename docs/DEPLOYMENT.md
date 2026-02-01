# Deployment Guide

> Hướng dẫn triển khai MusicMoodBot v1.0

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Local Development](#2-local-development)
3. [Production Deployment](#3-production-deployment)
4. [Environment Configuration](#4-environment-configuration)
5. [Monitoring](#5-monitoring)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Tổng quan

### 1.1 Deployment Options

| Option | Use Case | Complexity |
|--------|----------|------------|
| Local | Development, Testing | Low |
| Docker | Staging, Production | Medium |
| Cloud (Azure/AWS) | Enterprise Production | High |

### 1.2 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Storage | 1 GB | 5 GB |
| Python | 3.12 | 3.12+ |

---

## 2. Local Development

### 2.1 Quick Start

```bash
# Clone repository
git clone https://github.com/Duc1445/MusicMoodBot.git
cd MusicMoodBot

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
python run_app.py
```

### 2.2 Development Mode

```bash
# Backend only (with hot reload)
cd backend
uvicorn main:app --reload --port 8000

# Frontend only
cd frontend
python main.py
```

### 2.3 Verify Installation

```bash
# Check backend health
curl http://localhost:8000/health

# Expected response
{
  "status": "healthy",
  "database": "connected"
}
```

---

## 3. Production Deployment

### 3.1 Pre-deployment Checklist

| Task | Status | Notes |
|------|--------|-------|
| [ ] Set production environment variables | | See Section 4 |
| [ ] Generate strong JWT secret | | Use secrets generator |
| [ ] Enable HTTPS | | Required for auth |
| [ ] Configure firewall | | Allow port 443 only |
| [ ] Set up database backups | | Daily recommended |
| [ ] Configure logging | | Centralized logging |
| [ ] Test all endpoints | | Run test suite |

### 3.2 Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose:**
```yaml
version: '3.8'

services:
  musicmoodbot:
    build: .
    ports:
      - "8000:8000"
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - DEBUG=false
    volumes:
      - ./data:/app/backend/src/database
    restart: unless-stopped
```

**Commands:**
```bash
# Build
docker build -t musicmoodbot:latest .

# Run
docker run -d -p 8000:8000 --name mmb musicmoodbot:latest

# View logs
docker logs -f mmb
```

### 3.3 Windows Service (Production)

**Install as Windows Service:**
```powershell
# Using NSSM (Non-Sucking Service Manager)
nssm install MusicMoodBot "C:\Python312\python.exe" "C:\MusicMoodBot\run_app.py"
nssm set MusicMoodBot AppDirectory "C:\MusicMoodBot"
nssm set MusicMoodBot Description "Music Mood Bot Service"
nssm start MusicMoodBot
```

### 3.4 Linux Systemd Service

**/etc/systemd/system/musicmoodbot.service:**
```ini
[Unit]
Description=MusicMoodBot Service
After=network.target

[Service]
Type=simple
User=mmb
WorkingDirectory=/opt/musicmoodbot
Environment="PATH=/opt/musicmoodbot/.venv/bin"
ExecStart=/opt/musicmoodbot/.venv/bin/python run_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Commands:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable musicmoodbot
sudo systemctl start musicmoodbot
sudo systemctl status musicmoodbot
```

---

## 4. Environment Configuration

### 4.1 Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `API_BASE_URL` | Base URL for API | `http://localhost:8000` | Yes |
| `API_TIMEOUT` | Request timeout (seconds) | `30` | No |
| `JWT_SECRET_KEY` | JWT signing key | - | Yes (prod) |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` | No |
| `JWT_EXPIRATION_HOURS` | Token expiration | `24` | No |
| `DEBUG` | Debug mode | `false` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### 4.2 Production .env Example

```env
# API Configuration
API_BASE_URL=https://api.yourdomain.com
API_TIMEOUT=30

# Security (IMPORTANT: Use strong random values)
JWT_SECRET_KEY=your-256-bit-secret-key-here-make-it-long-and-random
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Environment
DEBUG=false
LOG_LEVEL=WARNING

# Database
DB_PATH=/opt/musicmoodbot/data/music.db
```

### 4.3 Generate JWT Secret

```python
import secrets
print(secrets.token_urlsafe(32))
# Output: 8dG_kL2mN4oP6qR8sT0uV2wX4yZ6...
```

---

## 5. Monitoring

### 5.1 Health Check Endpoint

```bash
# Automated health check
curl -s http://localhost:8000/health | jq .

# Expected output
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2025-02-01T12:00:00Z"
}
```

### 5.2 Logging Configuration

**Log Levels:**
| Level | Use Case |
|-------|----------|
| DEBUG | Development only |
| INFO | Normal operations |
| WARNING | Production recommended |
| ERROR | Critical issues only |

**Log Format:**
```
2025-02-01 12:00:00 - INFO - Request: GET /health - 200 - 15ms
2025-02-01 12:00:01 - INFO - User login: duc - success
2025-02-01 12:00:02 - WARNING - Rate limit exceeded: 192.168.1.1
```

### 5.3 Performance Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Response Time (p95) | < 200ms | > 500ms |
| Error Rate | < 1% | > 5% |
| CPU Usage | < 50% | > 80% |
| Memory Usage | < 70% | > 90% |
| Database Connections | < 10 | > 50 |

---

## 6. Troubleshooting

### 6.1 Common Issues

#### Issue: Server không khởi động

**Symptoms:**
- Port already in use error
- Module not found error

**Solutions:**
```bash
# Check port usage
netstat -ano | findstr :8000

# Kill process using port
taskkill /PID <pid> /F

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

#### Issue: Database locked

**Symptoms:**
- SQLite database is locked error
- Timeout waiting for database

**Solutions:**
```bash
# Check for lock file
ls backend/src/database/*.db-*

# Remove stale locks (careful!)
rm backend/src/database/*.db-wal
rm backend/src/database/*.db-shm

# Restart service
```

---

#### Issue: JWT Token Invalid

**Symptoms:**
- 401 Unauthorized errors
- "Token expired" message

**Solutions:**
1. Check server time synchronization
2. Verify JWT_SECRET_KEY matches between restarts
3. Clear client-side token storage
4. Re-login

---

#### Issue: Mood Detection Inaccurate

**Symptoms:**
- Wrong mood detected
- Low confidence scores

**Solutions:**
1. Ensure Vietnamese text input
2. Check for typos in keywords
3. Use longer, more descriptive text

---

### 6.2 Debug Commands

```bash
# Check running processes
ps aux | grep python

# View real-time logs
tail -f /var/log/musicmoodbot/app.log

# Test database connection
python -c "import sqlite3; c=sqlite3.connect('backend/src/database/music.db'); print('OK')"

# Test API endpoint
curl -X POST http://localhost:8000/api/recommendations/detect-mood \
  -H "Content-Type: application/json" \
  -d '{"text": "tôi vui quá"}'
```

### 6.3 Contact Support

| Issue Type | Contact |
|------------|---------|
| Bug Report | GitHub Issues |
| Security | security@musicmoodbot.com |
| General | support@musicmoodbot.com |

---

## Appendix

### A. Port Configuration

| Service | Default Port | Configurable |
|---------|--------------|--------------|
| Backend API | 8000 | Yes |
| Frontend (Desktop) | N/A | N/A |

### B. Backup Script

```bash
#!/bin/bash
# backup.sh - Daily database backup

DATE=$(date +%Y%m%d)
BACKUP_DIR=/backups/musicmoodbot
DB_PATH=/opt/musicmoodbot/data/music.db

mkdir -p $BACKUP_DIR
sqlite3 $DB_PATH ".backup '$BACKUP_DIR/music_$DATE.db'"

# Keep only last 7 days
find $BACKUP_DIR -name "*.db" -mtime +7 -delete

echo "Backup completed: music_$DATE.db"
```

### C. SSL/HTTPS Configuration (Nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name api.musicmoodbot.com;

    ssl_certificate /etc/letsencrypt/live/api.musicmoodbot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.musicmoodbot.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

*Document Version: 1.0.0*
*Last Updated: February 2025*
