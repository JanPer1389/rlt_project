from typing import List, Any, TypeVar, Generic
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, func
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from dao.models import User
from datetime import date
from dao.database import Base

# Объявляем типовой параметр T с ограничением, что это наследник Base
T = TypeVar("T", bound=Base)


class BaseDAO(Generic[T]):
    model: type[T]

    @classmethod
    async def find_one_or_none(cls, session: AsyncSession, filters: BaseModel):
        filters_dict = filters.model_dump(exclude_unset=True)
        logger.info(f'Проводим поиск по {filters_dict}')
        try:
            query = select(cls.model).filter_by(**filters_dict)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            if record:
                logger.info(f'Запись найдена по фильтрам {filters_dict}')
            else:
                logger.info(f'Запись по фильтрам {filters_dict} не найдена(')
            
            return record
        
        except SQLAlchemyError as e:
            logger.error(f'Поиск неудался, ошибка {e}')
            await session.rollback()
            raise e
    
    @classmethod
    async def find_one_or_none_by_id(cls, session: AsyncSession, data_id: int):
        logger.info (f'Проводим поиск по id {data_id}')
        try:
            query = select(cls.model).filter_by(id=data_id)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            return record
        except SQLAlchemyError as e:
            await session.rollback()
            raise e
    
    @classmethod
    async def delete (cls, session: AsyncSession, filter: BaseModel):
        filter_dict = filter.model_dump(exclude_unset=True)
        logger.info(f'Удаление записей {cls.model.__name__} по фильтру {filter_dict}')
        if not filter_dict:
            logger.error('Нужен хотя бы один фильтр для удаления')
            raise ValueError ('Нужен хотя бы один фильтр')
        
        query = sqlalchemy_delete(cls.model).filter_by(**filter_dict)
        try:
            result = await session.execute(query)
            await session.flush()
            logger.info(f'Удалено {result.rowcount} записей')
            return result.rowcount
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f'Ошибка при удалении записей {e}')
            raise e
    
    @classmethod
    async def count(cls, session: AsyncSession, filter: BaseModel | None = None):
        filter_dict = filter.model_dump(exclude_unset=True) if filter else {}
        logger.info(f'Подсчитываем записи {cls.model.__name__} по фильтру {filter_dict}')
        try:
            query = select(func.count(cls.model)).filter_by(**filter_dict)
            result = await session.execute(query)
            count = result.scalar()
            logger.info (f'Найдено {count}')
        except SQLAlchemyError as e:
            logger.error(f'Ошибка при подсчете записей {e}')
            raise e