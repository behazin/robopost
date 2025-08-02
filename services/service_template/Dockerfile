FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Add shared library and service code
COPY common_utils ./common_utils
COPY . ./service

CMD ["python", "service/app.py"]
