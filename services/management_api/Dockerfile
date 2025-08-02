FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app

COPY services/management_api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY common_utils ./common_utils
COPY services/management_api/ ./service

CMD ["uvicorn", "service.main:app", "--host", "0.0.0.0", "--port", "8000"]
