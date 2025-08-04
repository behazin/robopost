FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app

# Install dependencies
COPY services/publisher_service/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Add shared library and service code
COPY common_utils ./common_utils
COPY services/publisher_service/ ./service

CMD ["python", "service/app.py"]