import random

async def human_scroll(page, locator, times: int = 1):
	"""
	Scroll giống hành vi người dùng thật
	:param page: playwright page
	:param locator: locator video items
	:param times: số lần scroll
	"""
	for i in range(times):
		count = await locator.count()
		if count == 0:
			break

		# Move mouse nhẹ (giống người)
		await page.mouse.move(
			random.randint(200, 600),
			random.randint(200, 500)
		)

		# Scroll tới item cuối
		await locator.nth(count - 1).scroll_into_view_if_needed()

		# dừng xem ngắn
		await page.wait_for_timeout(random.randint(800, 1500))

		# 🔄 20% scroll ngược lại
		if random.random() < 0.2:
			await page.mouse.wheel(0, -random.randint(150, 300))
			await page.wait_for_timeout(random.randint(200, 400))

		# 😵‍💫 10% đứng im rất lâu (lướt mà quên scroll)
		if random.random() < 0.1:
			long_pause = random.randint(6000, 12000)
			await page.wait_for_timeout(long_pause)

		# Người dùng thường dừng xem
		await page.wait_for_timeout(random.randint(700, 1200))