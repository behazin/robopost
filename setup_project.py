from pathlib import Path
from textwrap import dedent

FILES = {
    ".env.example": dedent("""\
        # MySQL configuration
        MYSQL_ROOT_PASSWORD=rootpassword
        MYSQL_USER=app_user
        MYSQL_PASSWORD=app_password
        MYSQL_DB=app_db
        MYSQL_HOST=mysql
        MYSQL_PORT=3306

        # RabbitMQ configuration
        RABBITMQ_USER=guest
        RABBITMQ_PASSWORD=guest
        RABBITMQ_HOST=rabbitmq
        RABBITMQ_PORT=5672

        # Logging
        LOG_LEVEL=INFO
    """),
    ".gitignore": dedent("""\
        # Byte-compiled / optimized / DLL files
        __pycache__/
        *.py[cod]

        # Virtual environments
        .venv/
        venv/

        # Environment variables
        .env
        .env.*
        !.env.example

        # Python egg metadata, build, and dist
        build/
        dist/
        *.egg-info/

        # Logs
        *.log

        # Pytest and coverage
        .pytest_cache/
        .coverage
        htmlcov/

        # IDE directories
        .vscode/
        .idea/

        # Docker
        **/Dockerfile~
        .DS_Store
    """),
    ".github/workflows/ci.yml": dedent("""\
        name: CI

        on:
          push:
            branches: [ main ]
          pull_request:
            branches: [ main ]

        jobs:
          lint:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v3
              - uses: actions/setup-python@v4
                with:
                  python-version: '3.11'
              - name: Install dependencies
                run: |
                  python -m pip install --upgrade pip
                  pip install flake8
              - name: Run lint
                run: flake8 common_utils services

          build:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v3
              - name: Build Docker image
                run: docker build -t service-template ./services/service_template
    """),
    "common_utils/__init__.py": dedent("""\
        from .db import get_engine, get_session
        from .rabbitmq import get_rabbitmq_connection
        from .logging import configure_logging

        __all__ = [
            "get_engine",
            "get_session",
            "get_rabbitmq_connection",
            "configure_logging",
        ]
    """),
    "common_utils/db.py": dedent("""\
        import os
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        _engine = None
        _SessionLocal = None


        def _get_db_url() -> str:
            user = os.getenv("MYSQL_USER", "root")
            password = os.getenv("MYSQL_PASSWORD", "")
            host = os.getenv("MYSQL_HOST", "localhost")
            port = os.getenv("MYSQL_PORT", "3306")
            db = os.getenv("MYSQL_DB", "app")
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"


        def get_engine():
            global _engine
            if _engine is None:
                _engine = create_engine(_get_db_url(), pool_pre_ping=True)
            return _engine


        def get_session():
            global _SessionLocal
            if _SessionLocal is None:
                _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
            return _SessionLocal()
    """),
    "common_utils/logging.py": dedent("""\
        import logging
        import os
        from pythonjsonlogger import jsonlogger


        def configure_logging():
            level = os.getenv("LOG_LEVEL", "INFO").upper()
            logger = logging.getLogger()
            if logger.handlers:
                return logger

            handler = logging.StreamHandler()
            formatter = jsonlogger.JsonFormatter()
            handler.setFormatter(formatter)
            logger.setLevel(level)
            logger.addHandler(handler)
            return logger
    """),
    "common_utils/rabbitmq.py": dedent("""\
        import os
        import pika


        def get_rabbitmq_connection():
            user = os.getenv("RABBITMQ_USER", "guest")
            password = os.getenv("RABBITMQ_PASSWORD", "guest")
            host = os.getenv("RABBITMQ_HOST", "localhost")
            port = int(os.getenv("RABBITMQ_PORT", "5672"))

            credentials = pika.PlainCredentials(user, password)
            parameters = pika.ConnectionParameters(host=host, port=port, credentials=credentials)
            return pika.BlockingConnection(parameters)
    """),
    "docker-compose.yml": dedent("""\
        version: '3.9'

        services:
          mysql:
            image: mysql:8
            restart: always
            environment:
              MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
              MYSQL_DATABASE: ${MYSQL_DB}
              MYSQL_USER: ${MYSQL_USER}
              MYSQL_PASSWORD: ${MYSQL_PASSWORD}
            ports:
              - "3306:3306"
            volumes:
              - mysql_data:/var/lib/mysql

          rabbitmq:
            image: rabbitmq:3-management
            restart: always
            environment:
              RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
              RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
            ports:
              - "5672:5672"
              - "15672:15672"

          service_template:
            build: ./services/service_template
            environment:
              MYSQL_USER: ${MYSQL_USER}
              MYSQL_PASSWORD: ${MYSQL_PASSWORD}
              MYSQL_DB: ${MYSQL_DB}
              MYSQL_HOST: mysql
              MYSQL_PORT: 3306
              RABBITMQ_USER: ${RABBITMQ_USER}
              RABBITMQ_PASSWORD: ${RABBITMQ_PASSWORD}
              RABBITMQ_HOST: rabbitmq
              RABBITMQ_PORT: 5672
              LOG_LEVEL: ${LOG_LEVEL}
            depends_on:
              - mysql
              - rabbitmq

        volumes:
          mysql_data:
    """),
    "services/service_template/Dockerfile": dedent("""\
        FROM python:3.11-slim

        WORKDIR /app

        # Install dependencies
        COPY requirements.txt ./
        RUN pip install --no-cache-dir -r requirements.txt

        # Add shared library and service code
        COPY ../../common_utils ./common_utils
        COPY . ./service

        CMD ["python", "service/app.py"]
    """),
    "services/service_template/app.py": dedent("""\
        from common_utils import (
            configure_logging,
            get_rabbitmq_connection,
            get_session,
        )


        def main():
            logger = configure_logging()
            logger.info("Service template starting")
            db = get_session()
            conn = get_rabbitmq_connection()
            logger.info("Connections to MySQL and RabbitMQ established")
            conn.close()
            db.close()


        if __name__ == "__main__":
            main()
    """),
    "services/service_template/requirements.txt": dedent("""\
        pika
        SQLAlchemy
        pymysql
        python-json-logger
    """),
    "services/service_template/__init__.py": "",
}


def create_structure(base_dir: str = ".") -> None:
    base = Path(base_dir)
    for rel_path, content in FILES.items():
        file_path = base / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    create_structure()
    print("ساختار پروژه ایجاد شد.")
