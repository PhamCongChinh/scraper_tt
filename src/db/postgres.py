import asyncpg

from datetime import datetime, timedelta, timezone

VN_TZ = timezone(timedelta(hours=7))

class PostgresDB:
    pool = None
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                user="anhquan",
                password="123456",
                database="for_demo",
                host="222.254.14.6",
                port=5433,
                min_size=10,
                max_size=50,   # tăng nếu crawl mạnh
                command_timeout=60
            )
            print("✅ Connected PostgreSQL")

    async def close(self):
        if self.pool:
            await self.pool.close()
            print("❌ Closed PostgreSQL")

    async def fetch_posts(self, limit=10):
        now_ts = int(datetime.now(tz=timezone.utc).timestamp())
        start, end = self.get_day_range(now_ts)
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, org_id, url
                FROM tbl_posts
                WHERE crawl_source_code = 'tt'
                AND pub_time >= $1
                AND pub_time < $2
                ORDER BY id DESC
                LIMIT $3
            """, 1709289214, end, limit)
            return [dict(row) for row in rows]
        
    def get_day_range(self, ts: int):
        # dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        # start = int(datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc).timestamp())
        # end = start + 86400
        # return start, end
        dt = datetime.fromtimestamp(ts, tz=VN_TZ)
        start = int(datetime(dt.year, dt.month, dt.day, tzinfo=VN_TZ).timestamp())
        end = start + 86400
        return start, end