from datetime import datetime
from bot.config import database_url
from sqlalchemy import func, TIMESTAMP, Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession

engine = create_async_engine(url=database_url)

async_session_maker = async_sessionmaker(engine, class_=AsyncSession)

class Base (AsyncAttrs, DeclarativeBase):
    __abstract__ = True
    

    @classmethod
    @property

    def __tablename__(cls) -> str:
        return cls.__name__.lower() + 's'