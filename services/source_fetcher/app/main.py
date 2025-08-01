import asyncio
import os
import logging
from dotenv import load_dotenv

load_dotenv()

from .fetcher import Fetcher
from .db import SessionLocal
from .rabbitmq import RabbitMQClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    fetch_interval = int(os.getenv("FETCH_INTERVAL_SECONDS", 60))
    
    # Initialize components
    db_session = SessionLocal()
    rabbit_client = RabbitMQClient(os.getenv("RABBITMQ_URL"))
    
    fetcher = Fetcher(db_session, rabbit_client)

    try:
        await rabbit_client.connect()
        logging.info("Source Fetcher service started.")
        while True:
            logging.info("Starting new fetch cycle...")
            await fetcher.fetch_all_sources()
            logging.info(f"Fetch cycle finished. Waiting for {fetch_interval} seconds.")
            await asyncio.sleep(fetch_interval)
    except Exception as e:
        logging.error(f"A critical error occurred: {e}")
    finally:
        await fetcher.close()
        logging.info("Source Fetcher service stopped.")

if __name__ == "__main__":
    asyncio.run(main())