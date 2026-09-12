from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    bot_token: str = os.environ.get('BOT_TOKEN', '')
    admin_telegram_id: int = int(os.environ.get('ADMIN_TELEGRAM_ID', '0'))
    database_url: str = os.environ.get('DATABASE_URL', 'sqlite+aiosqlite:///./data/tutor.db')
    low_balance_kopecks: int = int(os.environ.get('LOW_BALANCE_KOPECKS', '100000'))
    timezone: str = os.environ.get('TIMEZONE', 'Europe/Berlin')
    lesson_generation_days: int = int(os.environ.get('LESSON_GENERATION_DAYS', '90'))
    log_level: str = os.environ.get('LOG_LEVEL', 'INFO')

settings = Settings()
