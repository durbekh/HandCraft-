version: "3.9"

services:
  # ─── PostgreSQL ────────────────────────────────────────────────
  db:
    image: postgres:15-alpine
    container_name: handcraft_db
    restart: unless-stopped
    volumes:
      - postgres_data:/var/lib/postgresql/data
    env_file:
      - .env
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-handcraft}
      POSTGRES_USER: ${POSTGRES_USER:-handcraft_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-handcraft_pass}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-handcraft_user} -d ${POSTGRES_DB:-handcraft}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ─── Redis ─────────────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    container_name: handcraft_redis
    restart: unless-stopped
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ─── Elasticsearch ─────────────────────────────────────────────
  elasticsearch:
    image: elasticsearch:8.11.0
    container_name: handcraft_elasticsearch
    restart: unless-stopped
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "${ELASTICSEARCH_PORT:-9200}:9200"
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # ─── Django Backend ────────────────────────────────────────────
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: handcraft_backend
    restart: unless-stopped
    command: >
      sh -c "python manage.py migrate --noinput &&
             python manage.py collectstatic --noinput &&
             gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120"
    volumes:
      - ./backend:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    env_file:
      - .env
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.development
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      elasticsearch:
        condition: service_healthy

  # ─── Celery Worker ─────────────────────────────────────────────
  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: handcraft_celery_worker
    restart: unless-stopped
    command: celery -A config worker -l info --concurrency=4
    volumes:
      - ./backend:/app
    env_file:
      - .env
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.development
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  # ─── Celery Beat (Scheduler) ───────────────────────────────────
  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: handcraft_celery_beat
    restart: unless-stopped
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    volumes:
      - ./backend:/app
    env_file:
      - .env
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.development
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  # ─── Next.js Frontend ─────────────────────────────────────────
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: handcraft_frontend
    restart: unless-stopped
    command: npm run dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    env_file:
      - .env
    environment:
      - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:8000/api/v1}
    ports:
      - "3000:3000"
    depends_on:
      - backend

  # ─── Nginx Reverse Proxy ───────────────────────────────────────
  nginx:
    image: nginx:1.25-alpine
    container_name: handcraft_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/var/www/static
      - media_volume:/var/www/media
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  elasticsearch_data:
    driver: local
  static_volume:
    driver: local
  media_volume:
    driver: local
