# Versión de Python: debe coincidir con la que usas en local (python --version)
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 1) Dependencias primero: Docker reutiliza esta capa si requirements.txt no cambia
COPY requirements.txt .
RUN pip install -r requirements.txt

# 2) Código del proyecto
COPY . .

# 3) Usuario sin privilegios, carpeta de datos y archivos estáticos
RUN useradd --create-home appuser \
    && mkdir -p /data \
    && python manage.py collectstatic --noinput \
    && chown -R appuser:appuser /app /data
USER appuser

ENV DJANGO_DB_PATH=/data/db.sqlite3
EXPOSE 8000

# Aplica las migraciones y arranca gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2"]