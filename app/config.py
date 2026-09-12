import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self.APP_ENV = os.getenv("APP_ENV", "development")
        self.API_KEY = os.getenv("API_KEY", "dev-api-key")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "5"))
        self.RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
        self.DATABASE_URL = os.getenv("DATABASE_URL", "")
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        self.validate_environment()

    def validate_environment(self):
        if self.APP_ENV == "production":
            missing = []
            if not self.API_KEY or self.API_KEY == "dev-api-key":
                missing.append("API_KEY")
            if not self.DATABASE_URL:
                missing.append("DATABASE_URL")
            if not self.GROQ_API_KEY:
                missing.append("GROQ_API_KEY")
            if missing:
                raise ValueError(f"Missing required production secrets: {', '.join(missing)}")


settings = Settings()
