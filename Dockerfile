
FROM python:3.11-alpine3.19

WORKDIR /app

RUN apk update && apk upgrade

RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    python3-dev \
    libffi-dev \
    && rm -rf /var/cache/apk/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser -D -s /bin/sh appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000


HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "main.py"]