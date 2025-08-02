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
