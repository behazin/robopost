FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app

COPY services/core_engine/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY common_utils ./common_utils
COPY services/core_engine/ ./service

CMD ["python", "service/app.py"]