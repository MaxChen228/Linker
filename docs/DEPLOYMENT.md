# Deployment & Operations Guide

## Prerequisites

- Python 3.9+
- 2GB RAM minimum
- 10GB disk space
- Internet connectivity for AI API access

## Environment Variables

```bash
# Required
GEMINI_API_KEY=your-api-key

# Optional - For Database Mode
USE_DATABASE=true
DATABASE_URL=postgresql://user:password@host:port/dbname

# Optional - General
GEMINI_GENERATE_MODEL=gemini-2.5-flash  # Default
GEMINI_GRADE_MODEL=gemini-2.5-pro       # Default
LOG_LEVEL=INFO                          # INFO|DEBUG|WARNING|ERROR
PORT=8000                                # Server port
HOST=0.0.0.0                            # Bind address
```

## Database Configuration

By default, the application runs in JSON mode. To use a PostgreSQL database, follow these steps:

1.  **Set Up PostgreSQL**: Ensure you have a running PostgreSQL server.

2.  **Set Environment Variables**: Set `USE_DATABASE` and `DATABASE_URL` as shown above.

    ```bash
    export USE_DATABASE=true
    export DATABASE_URL="postgresql://your_user:your_password@your_host:5432/linker"
    ```

3.  **Initialize the Database**: Run the initialization script to create all the necessary tables and indexes. This only needs to be done once.

    ```bash
    python scripts/init_database.py
    ```

4.  **Run Data Migration (Optional)**: If you have existing data in `data/knowledge.json` that you want to move to the database, run the migration script.

    ```bash
    python scripts/migrate_data.py
    ```

5.  **Start the Application**: Run the application as usual. It will now use the database as its backend.

    ```bash
    ./run.sh
    ```

## Deployment Options

### 1. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn web.main:app --reload --port 8000
```

### 2. Production Server

```bash
# Install production dependencies
pip install -r requirements.txt
pip install gunicorn

# Run with Gunicorn (4 workers)
gunicorn web.main:app -w 4 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### 3. Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t linker .
docker run -p 8000:8000 -e GEMINI_API_KEY=your-key linker
```

### 4. Docker Compose

This is an example for running in database mode.

```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - USE_DATABASE=true
      - DATABASE_URL=${DATABASE_URL} # e.g., postgresql://user:pass@host/db
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

### 5. Cloud Deployment

#### Render.com
1. Connect GitHub repository
2. Set environment variables in dashboard
3. Deploy with `render.yaml`:

```yaml
services:
  - type: web
    name: linker
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn web.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GEMINI_API_KEY
        sync: false
```

#### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway up
```

#### Google Cloud Run
```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/linker

# Deploy
gcloud run deploy linker \
  --image gcr.io/PROJECT_ID/linker \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your-key
```

## System Monitoring

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/api/health

# Detailed status
curl http://localhost:8000/api/health?detailed=true
```

### Logging

Logs are written to:
- Console (stdout/stderr)
- `logs/linker.log` (rotating daily)
- `logs/error.log` (errors only)

### Metrics to Monitor

1. **Application Metrics**
   - Request rate and latency
   - Error rate (4xx, 5xx)
   - Active sessions

2. **AI Service Metrics**
   - API call success rate
   - Response time
   - Token usage

3. **System Metrics**
   - CPU usage (target < 70%)
   - Memory usage (target < 80%)
   - Disk I/O

## Maintenance Tasks

### Daily
- Check error logs for anomalies
- Monitor AI API quota usage

### Weekly
- Backup data files (`data/*.json`)
- Review performance metrics
- Update dependencies if security patches available

### Monthly
- Clean old log files
- Review and optimize slow queries
- Update documentation if needed

## Backup & Recovery

### Backup Strategy
```bash
# Automated daily backup
0 2 * * * tar -czf /backup/linker-$(date +\%Y\%m\%d).tar.gz /app/data
```

### Recovery Process
```bash
# Restore from backup
tar -xzf /backup/linker-20240115.tar.gz -C /
systemctl restart linker
```

## Troubleshooting

### Common Issues

1. **AI Service Connection Failed**
   - Verify GEMINI_API_KEY is set correctly
   - Check network connectivity
   - Verify API quota not exceeded

2. **High Memory Usage**
   - Restart application to clear caches
   - Check for memory leaks in logs
   - Consider increasing server RAM

3. **Slow Response Times**
   - Check AI API latency
   - Review application logs for bottlenecks
   - Consider implementing caching

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
./run.sh
```

View real-time logs:
```bash
tail -f logs/linker.log
```

## Security Checklist

- [ ] API keys stored in environment variables
- [ ] HTTPS enabled in production
- [ ] Regular security updates applied
- [ ] Access logs monitored for anomalies
- [ ] Rate limiting configured
- [ ] Input validation enabled
- [ ] XSS protection active

## Performance Tuning

### Optimization Tips

1. **Enable Response Caching**
   ```python
   # In settings.py
   CACHE_TTL_SECONDS = 300
   ```

2. **Adjust Worker Count**
   ```bash
   # Based on CPU cores
   workers = (2 * cpu_cores) + 1
   ```

3. **Database Connection Pooling**
   (Currently using JSON files, consider database for scale)

## Support

For production issues:
1. Check logs for error details
2. Review this guide's troubleshooting section
3. Create issue on GitHub with logs and environment details