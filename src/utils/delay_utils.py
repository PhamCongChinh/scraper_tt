import asyncio
import random


async def delay(min=2000, max=60000):
    await asyncio.sleep(random.uniform(min/1000, max/1000))

async def human_delay(min_ms=800, max_ms=1500):
	await asyncio.sleep(random.uniform(min_ms / 1000, max_ms / 1000))