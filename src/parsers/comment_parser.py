from datetime import datetime
from typing import Optional


class TiktokComment:

    BASE_URL = f"https://www.tiktok.com"
    crawl_source = 2
    crawl_source_code = 'tt'
    auth_type = 1
    source_type = 5
    crawl_bot = "tiktok-1"


    def _build_video_url(self, unique_id: str, post_id: Optional[str]) -> str:
        """Tạo URL video TikTok"""
        if not post_id:
            return ""
        return f"{self.BASE_URL}/@{unique_id}/video/{post_id}"
    
    def _build_author_url(self, unique_id: str) -> str:
        return f"{self.BASE_URL}/@{unique_id}"

    def new(self, data: dict):

        unique_id = data.get("unique_id", None)
        post_id = data.get("video_id", None)
        
        return {
            "doc_type": 2,
            "crawl_source": self.crawl_source,
            "crawl_source_code": self.crawl_source_code,
            "pub_time": data.get("pub_time", 0),
            "crawl_time": int(datetime.now().timestamp()),
            "subject_id": data.get("video_id", None),
            "title": data.get("title", None),
            "description": data.get("description", None),
            "content": data.get("description"),
            "url": self._build_video_url(unique_id, post_id),
            "media_urls": "[]",
            "comments": data.get("comments", 0),
            "shares": data.get("shares", 0),
            "reactions": data.get("reactions", 0),
            "favors": int(data.get("collectCount", 0) or 0),
            "views": data.get("views", 0),
            "web_tags": "[]",
            "web_keywords": "[]",
            "auth_id": data.get("auth_id", None),
            "auth_name": data.get("auth_name", None),
            "auth_type": self.auth_type,
            "auth_url": self._build_author_url(unique_id),
            "source_id": post_id,
            "source_type": self.source_type,
            "source_name": data.get("auth_name", None),
            "source_url": self._build_video_url(unique_id, post_id),
            "reply_to": None,
            "level": None,
            "sentiment": 0,
            "isPriority": False,
            "crawl_bot": self.crawl_bot
        }