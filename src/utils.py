from datetime import datetime, timedelta
import random
import asyncio
import json

# async def delay(min=2000, max=60000):
#     await asyncio.sleep(random.uniform(min/1000, max/1000))

# async def extract_video_info(page):
#     raw = await page.locator("#__UNIVERSAL_DATA_FOR_REHYDRATION__").inner_text()
#     data = json.loads(raw)
#     root = data["__DEFAULT_SCOPE__"]["webapp.video-detail"]["itemInfo"]["itemStruct"]

#     return {
#         "pub_time": int(root["createTime"]),
#         "description": root["desc"],
#         "video_id": root["id"],
#         "unique_id": root["author"]["uniqueId"],
#         "comments": root["stats"]["commentCount"],
#         "shares": root["stats"]["shareCount"],
#         "reactions": root["stats"]["diggCount"],
#         "favors": root["stats"]["collectCount"],
#         "views": root["stats"]["playCount"],
#         "auth_id": root["author"]["id"],
#         "auth_name": root["author"]["nickname"],
#     }


# def in_quiet_hours(start: int, end: int) -> bool:
#     hour = datetime.now().hour
#     if start < end:
#         return start <= hour < end
#     else:
#         return hour >= start or hour < end
    
# def seconds_until_quiet_end(start: int, end: int) -> int:
#     now = datetime.now()
#     today_end = now.replace(hour=end, minute=0, second=0, microsecond=0)

#     if in_quiet_hours(start, end):
#         if now.hour >= start:
#             today_end += timedelta(days=1)
#         return int((today_end - now).total_seconds())

#     return 0


# async def human_scroll(page, locator, times: int = 1):
#     for _ in range(times):
#         count = await locator.count()
#         if count < 3:
#             break

#         # 🖱️ Move mouse nhẹ
#         await page.mouse.move(
#             random.randint(120, 800),
#             random.randint(120, 600),
#             steps=random.randint(5, 15)
#         )

#         # 📌 Scroll tới item ngẫu nhiên gần cuối (đỡ bot)
#         target = random.randint(max(0, count - 4), count - 1)
#         await locator.nth(target).scroll_into_view_if_needed()

#         # ⏸️ Dừng xem
#         await page.wait_for_timeout(random.randint(1200, 3000))

#         # 🔄 Scroll ngược (20%)
#         if random.random() < 0.2:
#             await page.mouse.wheel(0, -random.randint(150, 400))
#             await page.wait_for_timeout(random.randint(300, 800))

#         # 😵‍💫 Đứng im rất lâu (10%)
#         if random.random() < 0.1:
#             await page.wait_for_timeout(random.randint(5000, 9000))

