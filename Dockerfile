FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY app /app/app
RUN pip install .
RUN python -m playwright install --with-deps chromium

CMD ["gunicorn","-b","0.0.0.0:8080","--timeout", "200","app.wsgi:app"]