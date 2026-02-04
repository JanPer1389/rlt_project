import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger
from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import database_url
from dao.models import User, Videos, Video_Snapshots

BASE_DIR = Path(__file__).parent.parent

engine = create_async_engine(url=database_url)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession)


def _model_columns(model) -> List[str]:
    return [column.name for column in model.__table__.columns]


def _schema_summary() -> str:
    lines = [
        "Схема базы данных (поля из моделей):",
        f"- users: {', '.join(_model_columns(User))}",
        f"- videos: {', '.join(_model_columns(Videos))}",
        f"- video_snapshots: {', '.join(_model_columns(Video_Snapshots))}",
    ]
    return "\n".join(lines)


def _configure_logging() -> None:
    log_path = BASE_DIR / "ai_db_agent.log"
    logger.remove()
    logger.add(log_path, format="{time} | {level} | {message}", level="INFO", rotation="5 MB")


async def _run_sql_query(query: str) -> List[Dict[str, Any]]:
    logger.info("Executing SQL query: {}", query)
    async with async_session_maker() as session:
        result = await session.execute(text(query))
        rows = result.fetchall()
        columns = result.keys()

    return [dict(zip(columns, row)) for row in rows]


# def _extract_single_number(text_value: str) -> str:
#     numbers = re.findall(r"-?\d+(?:[\s.,]\d+)*", text_value)
#     cleaned = [num.replace(" ", "").replace(",", ".") for num in numbers]
#     unique_numbers = [num for num in cleaned if num]
#     if len(unique_numbers) == 1:
#         return unique_numbers[0]
#     raise ValueError("Ответ должен содержать ровно одно число.")


async def ask_with_db(
    user_query: str,
    model: str = "deepseek/deepseek-v3.2",
    extra_context: str | None = None,
) -> str:
    _configure_logging()
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv('GPT_CREDENTIALS'),
    )


    user_content = f"{user_query}"
    if extra_context:
        user_content = f"{user_content}\n\nДополнительный контекст:\n{extra_context}"

    messages = [
        {
            "role": "system",
            "content": (
                        'Ты Ассистент, который работает с базой данных пользователя.' 
                        'В твоем наличии две базы - videos - здесь все о видео и videos_snapshots - они являются частью таблицы videos. В ней представлены части одного видео во времени, у них есть связь по id'
                        'В базе videos - следующие колонки: id, creator_id, video_created_at, views_count, likes_count, comments_count, reports_count, created_at, updated_at'
                        'В базе video_snapshots - следующие колонки: id, video_id, views_count, likes_count, comments_count, reports_count, delta_views_count, delta_likes_count, delta_comments_count, delta_reports_count, created_at и updated_at.'
                        'Твоя задача написать sql-запрос, который бы полностью удовлетворил пользователя и предоставил ему всю необходимую информацию'
                        'Пример: User: Сколько видео набрало больше 100 000 просмотров за всё время?; You: SELECT COUNT(id) FROM videos WHERE CAST(views_count AS INTEGER) > 100000;'
                        'Для выполнения задачи всегда обращайся к run_sql_query'
            ),
        },
        {
            "role": "user",
            "content": user_content,
        },
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tool_choice="auto",
    )
    message = response.choices[0].message

    follow_up = client.chat.completions.create(
        model=model,
        messages=messages,
        )
    return _run_sql_query(follow_up.choices[0].message.content)

    


def ask_with_db_sync(user_query: str, model: str = "deepseek/deepseek-v3.2") -> str:
    return asyncio.run(ask_with_db(user_query, model=model))