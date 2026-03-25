import asyncio
from datetime import datetime, time as dtime, timedelta
import json
import random
import time
import requests
from playwright.async_api import async_playwright
import urllib
from src.api import postToESUnclassified
from src.parsers.video_parser import TiktokPost
from src.db.mongo import MongoDB
from src.config.logging import setup_logging
import logging
from collections import defaultdict

from datetime import datetime
from zoneinfo import ZoneInfo

from src.utils.scroll_utils import human_scroll
from src.utils.delay_utils import delay
from src.utils.browser_actions import random_view_video
from src.utils.sleep_manager import SleepManager


setup_logging()
logger = logging.getLogger(__name__)

from src.config.settings import settings
from src.db.postgres import PostgresDB
postgresDB = PostgresDB()

TIKTOK_URL = "https://www.tiktok.com"
KEYWORDS = ["Xã Xuân Giang", "Hà Nội"]

API_FILTERS = [
	"/api/search/item/full/",
]
API_COMMENT = [
    "/api/comment/list/",  # API comment của TikTok
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
			await crawl_tiktok_search(browser, context, keywords, API_FILTERS)

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

		await crawl_tiktok_comment(context=context)

		# await crawl_tiktok_search(browser, context, KEYWORDS, API_FILTERS)

async def crawl_tiktok_comment(context):
	page = await context.new_page()
	await postgresDB.connect()
	posts = await postgresDB.fetch_posts(5)
	for i, row in enumerate(posts, 1):
		unix_time = int(time.time() * 1000)
		print(row.get("url"))
		url = row.get("url")

		await page.goto(url, wait_until="domcontentloaded")
		await page.wait_for_timeout(random.randint(60, 90))
		comments_by_video = {}
		async def on_response(res):
			if any(api in res.url for api in API_COMMENT):
				try:
					body = await res.json()
					print(body)
				except:
					return
				if not body:
					return

				comments = body.get("comments", [])

				# lấy video_id từ request URL
				import re
				# match = re.search(r"aweme_id=(\d+)", url)
				match = re.search(r"/video/(\d+)", url)
				video_id = match.group(1) if match else None

				if not video_id:
					return
				
				if video_id not in comments_by_video:
					comments_by_video[video_id] = []

				for c in comments:
					comment_id = c.get("cid")
					text = c.get("text")
					aweme_id = c.get("aweme_id") # subjectid
					create_time = c.get("create_time") #pubtime
					digg_count = c.get("digg_count")
					title = c.get("share_info").get("title")
					description = c.get("share_info").get("desc")
					content = c.get("share_info").get("desc")
					url = c.get("share_info").get("url")
					auth_id = c.get("share_info").get("uid")
					auth_name = c.get("share_info").get("nickname")
					unique_id = c.get("share_info").get("unique_id")



					comments_by_video[video_id].append({
						"comment_id": comment_id,
						"text": text
					})


				print(f"\n🎬 VIDEO ID: {video_id}")
				print(f"💬 TOTAL COMMENTS FETCHED: {len(comments)}")
				print("=" * 50)

				for i, c in enumerate(comments, 1):
					comment_id = c.get("cid")
					text = c.get("text")
					user = c.get("user", {}).get("nickname")

					# comments_by_video[]

					print(f"{i}. 👤 {user}")
					print(f"   💬 {text}")
					print(f"   🆔 {comment_id}")
					print("-" * 50)

				# if not video_id:
				# 	return

				# if video_id not in comments_by_video:
				# 	comments_by_video[video_id] = []

				# for c in comments:
				# 	comment_id = c.get("cid")
				# 	text = c.get("text")

				# 	comments_by_video[video_id].append({
				# 		"comment_id": comment_id,
				# 		"text": text
				# 	})

		
		page.on("response", on_response)
		await asyncio.sleep(random.randint(10, 20))
		await close_popup_if_any(page)
		await asyncio.sleep(random.randint(10, 20))
		await page.click('[data-e2e="comment-icon"]')

		with open("comments.json", "w", encoding="utf-8") as f:
			json.dump(comments_by_video, f, ensure_ascii=False, indent=2)

		await asyncio.sleep(random.randint(60, 90))

	await postgresDB.close()
	rest_time = random.randint(600, 900)
	logger.info(f"😴 Resting {rest_time}s before next session")


async def close_popup_if_any(page):
    try:
        await page.locator('div[class*="DivXMarkWrapper"]').click(timeout=2000)
    except:
        pass

async def crawl_tiktok_search(browser, context, KEYWORDS, API_FILTERS):

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

		await page.goto("https://www.tiktok.com", wait_until="domcontentloaded")
		await page.wait_for_load_state("domcontentloaded")
		await page.wait_for_timeout(random.randint(4000, 7000))

		await page.mouse.move(
			random.randint(100, 900),
			random.randint(100, 600),
			steps=random.randint(10, 30)
		)
		await page.wait_for_timeout(random.randint(500, 1500))


		for keyword in batch_keywords:

			logger.info(f"[{keyword}] Search keyword: {keyword}")

			current_keyword = keyword
			videos_by_keyword[keyword] = []
			seen_ids_by_keyword[keyword] = set()

			unix_time = int(time.time() * 1000)
			encoded = urllib.parse.quote(keyword)
			search_url = f"https://www.tiktok.com/search/video?q={encoded}&t={unix_time}"

			await page.goto(search_url, wait_until="domcontentloaded")
			await page.wait_for_timeout(random.randint(6000, 9000))

			locator = page.locator("[id^='grid-item-container-']")

			await human_scroll(page, locator, times=random.randint(1, 4))
			await random_view_video(page)

			videos = videos_by_keyword[keyword]
			logger.info(f"[{keyword}] Total videos collected: {len(videos)}")

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
					logger.error(f"[{keyword}] Parse error: {e}")

			if results:
				try:
					result = await postToESUnclassified(results)
					logger.info(f"[{keyword}] Posted {len(results)} posts to API MASTER: {result.get('status')}")
				except Exception as e:
					logger.error(f"[{keyword}] Error posting to API MASTER: {e}")

			current_keyword = None
			time_sleep = random.randint(60, 120)
			logger.info(f"Waiting {time_sleep} seconds for the next keyword ...")
			await asyncio.sleep(time_sleep)

		logger.info(f"[{current_keyword}] 🛑 Closing page for rest period")

		await page.close()

		rest_time = random.randint(600, 900)
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
			sleep_manager = SleepManager(logger)
			# if sleep_manager.is_sleep_time():
			# 	await sleep_manager.sleep_until_wakeup()
			# 	continue
			
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