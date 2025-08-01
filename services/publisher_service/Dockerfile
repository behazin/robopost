FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app/app

CMD ["celery", "-A", "app.main.celery_app", "worker", "-l", "info", "-Q", "q.publication"]