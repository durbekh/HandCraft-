# ─── Core ─────────────────────────────────────────────────────────
Django==4.2.11
djangorestframework==3.14.0
gunicorn==21.2.0

# ─── Database ─────────────────────────────────────────────────────
psycopg2-binary==2.9.9

# ─── Authentication ──────────────────────────────────────────────
djangorestframework-simplejwt==5.3.1
django-allauth==0.61.1

# ─── CORS ─────────────────────────────────────────────────────────
django-cors-headers==4.3.1

# ─── Filtering & Search ─────────────────────────────────────────
django-filter==23.5
django-elasticsearch-dsl==8.0
django-elasticsearch-dsl-drf==0.22.5
elasticsearch==8.11.0
elasticsearch-dsl==8.11.0

# ─── File Storage (AWS S3) ───────────────────────────────────────
boto3==1.34.34
django-storages==1.14.2
Pillow==10.2.0

# ─── Celery & Redis ─────────────────────────────────────────────
celery==5.3.6
redis==5.0.1
django-redis==5.4.0
django-celery-beat==2.5.0
django-celery-results==2.5.1

# ─── Utilities ───────────────────────────────────────────────────
python-decouple==3.8
django-extensions==3.2.3
drf-spectacular==0.27.1
django-model-utils==4.4.0
shortuuid==1.0.11

# ─── Development & Testing ──────────────────────────────────────
pytest==8.0.0
pytest-django==4.8.0
pytest-cov==4.1.0
factory-boy==3.3.0
faker==22.6.0
flake8==7.0.0
black==24.1.1
isort==5.13.2
ipython==8.21.0

# ─── Monitoring ──────────────────────────────────────────────────
sentry-sdk==1.40.4
django-health-check==3.18.1
