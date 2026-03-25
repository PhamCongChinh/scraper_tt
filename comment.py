import asyncio
import logging

from src.config.logging import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

from src.config.settings import Settings
from src.db.postgres import PostgresDB

db = PostgresDB()

async def main():
    await db.connect()
    posts = await db.fetch_posts(20)

    for i, row in enumerate(posts, 1):
        print(f"Post {i}:")
        print(dict(row))
        print("-" * 50)
    

    await db.close()

if __name__ == "__main__":
	asyncio.run(main())