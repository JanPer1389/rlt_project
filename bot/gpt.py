import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import text

from dao.database import async_session_maker

BASE_DIR = Path(__file__).parent.parent


def _load_env() -> None:
    load_dotenv(dotenv_path=BASE_DIR / '.env')


def _validate_readonly_query(query: str) -> None:
    normalized = query.strip().lower()
    if not (normalized.startswith('select') or normalized.startswith('with')):
        raise ValueError('Разрешены только запросы SELECT/CTE')


async def _fetch_schema_summary() -> str:
    query = text(
        """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
        """
    )
    async with async_session_maker() as session:
        result = await session.execute(query)
        rows = result.fetchall()

    if not rows:
        return 'В базе данных нет таблиц в схеме public.'

    tables: Dict[str, List[str]] = {}
    for table_name, column_name, data_type in rows:
        tables.setdefault(table_name, []).append(f"{column_name} ({data_type})")

    lines = ['Схема базы данных:']
    for table_name, columns in tables.items():
        lines.append(f"- {table_name}: {', '.join(columns)}")
    return '\n'.join(lines)


async def _run_sql_query(query: str) -> List[Dict[str, Any]]:
    _validate_readonly_query(query)
    async with async_session_maker() as session:
        result = await session.execute(text(query))
        rows = result.fetchall()
        columns = result.keys()

    return [dict(zip(columns, row)) for row in rows]


async def ask_with_db(user_query: str, model: str = "deepseek/deepseek-v3.2") -> str:
    _load_env()
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv('GPT_CREDENTIALS'),
    )

    schema_summary = await _fetch_schema_summary()

    tools = [
        {
            "type": "function",
            "function": {
                "name": "run_sql_query",
                "description": "Выполняет read-only SQL запрос к Postgres и возвращает строки результата.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL запрос (только SELECT или WITH).",
                        }
                    },
                    "required": ["query"],
                },
            },
        }
    ]

    messages = [
        {
            "role": "system",
            "content": (
                "Ты помощник, который отвечает на вопросы по данным в базе Postgres. "
                "Используй инструмент run_sql_query для получения данных. "
                "Разрешены только SELECT/CTE запросы. Ответь кратко и по существу."
            ),
        },
        {
            "role": "user",
            "content": f"{user_query}\n\n{schema_summary}",
        },
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    message = response.choices[0].message

    if message.tool_calls:
        messages.append(message)
        for tool_call in message.tool_calls:
            if tool_call.function.name != 'run_sql_query':
                continue
            arguments = json.loads(tool_call.function.arguments)
            query = arguments.get('query', '')
            try:
                result = await _run_sql_query(query)
                tool_payload = json.dumps({"rows": result}, ensure_ascii=False)
            except Exception as exc:
                tool_payload = json.dumps({"error": str(exc)}, ensure_ascii=False)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": "run_sql_query",
                    "content": tool_payload,
                }
            )

        follow_up = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return follow_up.choices[0].message.content

    return message.content


def ask_with_db_sync(user_query: str, model: str = "deepseek/deepseek-v3.2") -> str:
    return asyncio.run(ask_with_db(user_query, model=model))