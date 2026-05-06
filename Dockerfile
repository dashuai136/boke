FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8080 \
    BEGONIA_DB=/data/begonia.db

COPY . /app

RUN mkdir -p /data

EXPOSE 8080

CMD ["sh", "-c", "python3 webapp/init_db.py && python3 webapp/app.py"]
