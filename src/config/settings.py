from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DEBUG: bool = False
    BOT_NAME: str
    DELAY: int = 5
    SLEEP: int = 60
    # GPM_API: str
    # PROFILE_ID: str

    # API: str = "http://localhost:8000"

    # REDIS_HOST: str = "localhost"
    # REDIS_PORT: int = 6379
    # REDIS_DB: int = 0
    # REDIS_PASSWORD: str = ""

    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "test_db"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    @property
    def POSTGRES_URI(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
