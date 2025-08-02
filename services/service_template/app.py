from common_utils import (
    configure_logging,
    get_rabbitmq_connection,
    session_scope,
)


def main():
    logger = configure_logging()
    logger.info("Service template starting")
    with session_scope() as db:
        conn = get_rabbitmq_connection()
        logger.info("Connections to MySQL and RabbitMQ established")
        conn.close()


if __name__ == "__main__":
    main()
