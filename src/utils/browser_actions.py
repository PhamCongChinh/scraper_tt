import random
from typing import Tuple


async def random_view_video(
    page,
    click_probability: float = 0.6,
    skip_click_probability: float = 0.3,
    comment_scroll_probability: float = 0.3,
    max_candidates: int = 5,
    watch_time_range: Tuple[int, int] = (8000, 25000),
) -> None:
    """
    Randomly hover/click a video element to simulate human behavior.
    """

    locator = page.locator("[id^='grid-item-container-']")
    count = await locator.count()

    if count == 0:
        return
    
    # ===== Random scroll trước khi chọn =====
    if random.random() < 0.7:
        await page.mouse.wheel(0, random.randint(200, 700))
        await page.wait_for_timeout(random.randint(800, 2000))

    # 60% xác suất mới tương tác
    if random.random() >= click_probability:
        return

    index = random.randint(0, min(count - 1, max_candidates))
    video = locator.nth(index)

    # Scroll tới video
    await video.scroll_into_view_if_needed()
    await page.wait_for_timeout(random.randint(800, 2000))

    # Di chuột tới vị trí random trong bounding box
    box = await video.bounding_box()
    # if box:
    #     x = box["x"] + random.randint(10, int(box["width"] - 10))
    #     y = box["y"] + random.randint(10, int(box["height"] - 10))

    #     await page.mouse.move(x, y, steps=random.randint(10, 25))
    #     await page.wait_for_timeout(random.randint(500, 1500))

    if box:
        start_x = box["x"] + random.randint(5, int(box["width"] - 5))
        start_y = box["y"] + random.randint(5, int(box["height"] - 5))

        # move nhiều step random
        for _ in range(random.randint(2, 4)):
            x = start_x + random.randint(-30, 30)
            y = start_y + random.randint(-30, 30)
            await page.mouse.move(x, y, steps=random.randint(5, 15))
            await page.wait_for_timeout(random.randint(200, 600))

    # Hover
    await video.hover()
    await page.wait_for_timeout(random.randint(1000, 2500))

    # 30% khả năng chỉ hover không click
    if random.random() < skip_click_probability:
        return

    # Click
    await video.click()

    # Xem video
    watch_time = random.randint(*watch_time_range)
    await page.wait_for_timeout(watch_time)

    # Scroll comment
    if random.random() < comment_scroll_probability:
        await page.mouse.wheel(0, random.randint(300, 800))
        await page.wait_for_timeout(random.randint(2000, 5000))

    await page.go_back()
    await page.wait_for_load_state("domcontentloaded")
    await page.wait_for_timeout(random.randint(3000, 6000))