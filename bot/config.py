import os
from typing import List
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent

class Settings(BaseSettings):
    BOT_TOKEN: str
    FORMAT_LOG: str = "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
    LOG_ROTATION: str = "10 MB"
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT:int
    DB_URL: str = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    )

settings = Settings()


bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher(storage=MemoryStorage())


database_url = settings.DB_URL

log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log.txt')
logger.add(log_file_path, format=settings.FORMAT_LOG, level='INFO', rotation=settings.LOG_ROTATION)