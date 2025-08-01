FROM python:3.9-slim

WORKDIR /app

# Copy and install the shared models library first
COPY ./shared/models /app/shared/models
RUN pip install --no-cache-dir -e ./shared/models

# Copy and install service-specific requirements
COPY ./services/api_gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./services/api_gateway/app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]