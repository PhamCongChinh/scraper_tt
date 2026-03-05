import asyncio
from datetime import datetime, time as dtime, timedelta
import random
import time
import requests
from playwright.async_api import async_playwright
import urllib
from src.api import postToESUnclassified
from src.parsers.video_parser import TiktokPost
from src.db.mongo import MongoDB
# from src.crawler_keywords import CrawlerKeyword
from src.config.logging import setup_logging
import logging
from collections import defaultdict

from datetime import datetime
from zoneinfo import ZoneInfo

# from src.utils import delay
from src.utils.scroll_utils import human_scroll
from src.utils.delay_utils import delay
from src.utils.browser_actions import random_view_video
from src.utils.sleep_manager import SleepManager


setup_logging()
logger = logging.getLogger(__name__)

from src.config.settings import settings

TIKTOK_URL = "https://www.tiktok.com"
KEYWORDS = ["Xã Xuân Giang", "Hà Nội"]

API_FILTERS = [
	"/api/search/item/full/",
]

SEARCH_API = "/api/search/item/full/"

db = MongoDB.get_db()
bot_config = db.tiktok_bot_configs

now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))

async def run_with_gpm():
	
	GPM_API = bot_config.find_one({"bot_name": f"{settings.BOT_NAME}"}).get("gpm_api")
	PROFILE_ID = bot_config.find_one({"bot_name": f"{settings.BOT_NAME}"}).get("profile_id")

	# ===== START PROFILE =====
	resp = requests.get(f"{GPM_API}/profiles/start/{PROFILE_ID}")
	resp.raise_for_status()

	data = resp.json()["data"]
	debug_addr = data["remote_debugging_address"]

	browser = None

	try:

		async with async_playwright() as p:
			browser = await p.chromium.connect_over_cdp(f"http://{debug_addr}")

			if not browser.contexts:
				raise Exception("No browser context found from GPM")

			context = browser.contexts[0]

			# Config từ MongoDB
			config = db.tiktok_bot_configs.find_one({"bot_name": settings.BOT_NAME})

			if not config:
				raise ValueError("Bot config not found")

			org_ids = config.get("org_id", [])
			org_ids_int = [int(x) for x in org_ids]

			keyword_col = db.keyword

			docs = list(keyword_col.find({
				"org_id": {"$in": org_ids_int}
			}))

			logger.info(f"Collection: {keyword_col.name}")
			logger.info(f"Total keywords: {len(docs)}")

			keywords = []

			for doc in docs:
				doc["_id"] = str(doc["_id"])
				keywords.append(doc["keyword"])

			await delay(1000, 2000)
			await crawl_tiktok_search_1(browser, context, keywords, API_FILTERS)

	except Exception as e:
		logger.exception(f"Error in run_with_gpm(): {e}")

	finally:
		# Đóng browser nếu còn mở
		try:
			if browser:
				await browser.close()
		except:
			pass

		# Stop GPM profile
		try:
			requests.get(f"{GPM_API}/profiles/close/{PROFILE_ID}")
			logger.info("GPM profile stopped")
		except Exception as e:
			logger.error(f"Failed to stop GPM profile: {e}")

async def run_test():
	async with async_playwright() as p:
		chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"  # đường dẫn Chrome trên Windows
		browser = await p.chromium.launch(
			headless=False,
			executable_path=chrome_path,
			args=["--disable-blink-features=AutomationControlled"]
		)
		context = await browser.new_context(storage_state="tiktok_profile.json")

		await crawl_tiktok_search_1(browser, context, KEYWORDS, API_FILTERS)

async def crawl_tiktok_search_1(browser, context, KEYWORDS, API_FILTERS):

	videos_by_keyword = defaultdict(list)
	seen_ids_by_keyword = defaultdict(set)

	BATCH_MIN = 5
	BATCH_MAX = 10

	i = 0
	total = len(KEYWORDS)

	while i < total:

		batch_size = random.randint(BATCH_MIN, BATCH_MAX)
		batch_keywords = KEYWORDS[i:i+batch_size]

		logger.info(f"🚀 New session with {len(batch_keywords)} keywords")

		page = await context.new_page()
		current_keyword = None

		async def on_response(res):
			nonlocal current_keyword

			if not current_keyword:
				return

			if any(api in res.url for api in API_FILTERS):
				try:
					body = await res.json()
				except:
					return

				if not body:
					return

				if body.get("status_code") == 0:
					items = body.get("item_list", [])

					for item in items:
						video_id = item.get("id")
						if not video_id:
							continue

						if video_id not in seen_ids_by_keyword[current_keyword]:
							seen_ids_by_keyword[current_keyword].add(video_id)
							videos_by_keyword[current_keyword].append(item)

		page.on("response", on_response)

		await page.goto("https://www.tiktok.com", timeout=60000)
		await page.wait_for_load_state("domcontentloaded")
		await page.wait_for_timeout(random.randint(4000, 7000))

		await page.mouse.move(
			random.randint(100, 900),
			random.randint(100, 600),
			steps=random.randint(10, 30)
		)
		await page.wait_for_timeout(random.randint(500, 1500))


		for keyword in batch_keywords:

			logger.info(f"Search keyword: {keyword}")

			current_keyword = keyword
			videos_by_keyword[keyword] = []
			seen_ids_by_keyword[keyword] = set()

			unix_time = int(time.time() * 1000)
			encoded = urllib.parse.quote(keyword)
			search_url = f"https://www.tiktok.com/search/video?q={encoded}&t={unix_time}"

			await page.goto(search_url, timeout=60000)
			await page.wait_for_timeout(random.randint(6000, 9000))

			locator = page.locator("[id^='grid-item-container-']")

			await human_scroll(page, locator, times=random.randint(1, 4))
			await random_view_video(page)

			videos = videos_by_keyword[keyword]
			logger.info(f"Total Videos collected: {len(videos)}")

			results = []
			now_ts = int(time.time())
			days_ago = now_ts - 7 * 24 * 60 * 60

			for item in videos:
				try:
					pub_time = int(item.get("createTime", 0))
					if pub_time < days_ago:
						continue

					video_info = {
						"keyword": keyword,
						"video_id": item.get("id"),
						"description": item.get("desc"),
						"pub_time": pub_time,
						"unique_id": item.get("author", {}).get("uniqueId", ""),
						"auth_id": item.get("author", {}).get("id", 0),
						"auth_name": item.get("author", {}).get("nickname", ""),
						"comments": item.get("stats", {}).get("commentCount", 0),
						"shares": item.get("stats", {}).get("shareCount", 0),
						"reactions": item.get("stats", {}).get("diggCount", 0),
						"favors": item.get("stats", {}).get("collectCount", 0),
						"views": item.get("stats", {}).get("playCount", 0)
					}

					data = TiktokPost().new(video_info)
					results.append(data)

				except Exception as e:
					logger.error(f"Parse error: {e}")

			logger.info(f"Parsed {len(results)} posts")

			if results:
				try:
					result = await postToESUnclassified(results)
					logger.info(f"Posted {len(results)} posts to API MASTER: {result.get('status')}")
				except Exception as e:
					logger.error(f"Error posting to API MASTER: {e}")

			current_keyword = None
			time_sleep = random.randint(60, 120)
			logger.info(f"Wating {time_sleep} second")
			await asyncio.sleep(time_sleep)

		logger.info("🛑 Closing page for rest period")
		await page.close()

		rest_time = random.randint(300, 600)
		logger.info(f"😴 Resting {rest_time}s before next session")
		await asyncio.sleep(rest_time)

		i += batch_size

	logger.info("🎉 Done crawling all keywords")

async def schedule():
	config = db.tiktok_bot_configs.find_one({"bot_name": settings.BOT_NAME})

	if not config:
		raise ValueError("Bot config not found")
	
	sleep = config.get("sleep", 5)
	logger.info(f"Sleep config in database: {sleep} minutes")

	INTERVAL = sleep * 60
	while True:
		try:
			logger.info(now)
			sleep_manager = SleepManager(logger)
			if sleep_manager.is_sleep_time():
				await sleep_manager.sleep_until_wakeup()
				continue
			
			if settings.DEBUG:
				await run_test()
			else:
				await run_with_gpm()

			logger.info(f"=== Run completed. Sleeping for {sleep} minutes ===")
		except Exception as e:
			logger.exception(f"Unhandled exception in run(): {e}")

		await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
	asyncio.run(schedule())