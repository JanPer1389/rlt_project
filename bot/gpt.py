import asyncio
import asyncpg
import re
from config import database_url
from pydantic import BaseModel, Field, field_validator
from openai import OpenAI
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator

from config import database_url


def to_asyncpg_dsn(url: str)->str:
    return url.replace('postgresql+asyncpg://', 'postgresql://',1)

FORBIDDEN = re.compile(r"\b(drop|delete|update|insert|alter|truncate|create|grant|revoke|copy)\b", re.IGNORECASE)


AGG = re.compile(r"\b(count|sum|avg|min|max)\s*\(", re.IGNORECASE)

class RunSQLInput(BaseModel):
    sql: str = Field(..., min_length=1, max_length=5000)

    @field_validator("sql")
    @classmethod
    def validate_and_normalize_sql(cls, v: str) -> str:
        s = v.strip()
        low = s.lower()

        if ";" in s:
            raise ValueError("Никаких ';'.")

        if not (low.startswith("select") or low.startswith("with")):
            raise ValueError("Разрешены только SELECT (включая WITH).")

        if FORBIDDEN.search(s):
            raise ValueError("Запрещены опасные команды SQL")

        if re.search(r"\blimit\b", s, re.IGNORECASE) is None:
            if not AGG.search(s):
                s += " LIMIT 50"

        return s


async def run_sql(sql: str):
    dsn = to_asyncpg_dsn(database_url)
    safe_sql = RunSQLInput(sql=sql).sql
    
    conn = await asyncpg.connect(dsn=dsn)
    try:
        rows = await conn.fetch(safe_sql)
        
        return [dict(r) for r in rows]
    finally:
        await conn.close()

async def get_schema_text()->str:
    dsn = to_asyncpg_dsn(database_url)
    conn = await asyncpg.connect(dsn)
    try:
        rows = await conn.fetch(
            """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
            """
        )
    finally:
        await conn.close()
    
    tables = {}
    
    for r in rows:
        tables.setdefault(r["table_name"], []).append(f"{r['column_name']} {r['data_type']}"
        )
    lines = []
    for t, cols in tables.items():
        lines.append(f'TABLE{t}: ' + ', '.join(cols))
    return '\n'.join(lines)

def llm_make_sql(client: OpenAI, question: str, schema_text: str) -> str:
    system = (
    "Ты помощник, который переводит вопрос пользователя в SQL для PostgreSQL.\n"
    "У тебя есть схема базы данных.\n"
    "Правила:\n"
    "- Разрешён только SELECT.\n"
    "- Никаких ';'.\n"
    "- Если считаешь количество — используй COUNT(*) и дай имя столбца cnt.\n"
    "- ВАЖНО: поля *_count часто хранятся как текст. Для сравнений и сумм всегда используй CAST(... AS INTEGER).\n"
    "- ВАЖНО: для фильтра по дате используй DATE(created_at) = 'YYYY-MM-DD' (или BETWEEN для диапазона).\n"
    "- Верни СТРОГО JSON без лишнего текста: {\"sql\": \"...\"}\n"
    "Если вопрос про на сколько выросли просмотры за дату D:"
    "- считай delta = last_views(D) - last_views(D-1) по каждому video_id"
    "- last_views(day) = views_count из последнего snapshot в этот день (по created_at)"
    "- views_count всегда CAST(... AS INTEGER)"
    )
    user = (
        "Схема БД:\n"
        f"{schema_text}\n\n"
        "Вопрос пользователя:\n"
        f"{question}\n"
    )
    
    resp = client.chat.completions.create(
        model = 'deepseek/deepseek-v3.2',
        messages=[
            {'role': "system", "content": system},
            {"role": "user", "content": user},
        ]
    )
    
    content = resp.choices[0].message.content
    
    return content

def extract_from_sql(text: str) -> str:
    if not text or not text.strip():
        raise ValueError("Модель вернула пустой ответ")

    s = text.strip()

   
    if s.startswith("```"):
        s = s.strip("`").strip()
   
        if s.lower().startswith("json"):
            s = s[4:].strip()

    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Не нашёл JSON в ответе модели: {s[:200]}")

    obj = json.loads(s[start:end + 1])
    if "sql" not in obj:
        raise ValueError(f"В JSON нет поля sql: {obj}")

    return obj["sql"]

def _load_env() -> None:
    base_dir = Path(__file__).parent.parent
    env_path = base_dir / ".env"
    load_dotenv(env_path)
    
def _build_client() -> OpenAI:
    _load_env()

    api_key = os.getenv("GPT_CREDENTIALS")
    if not api_key:
        raise RuntimeError("Не найден ключ GPT_CREDENTIALS в .env")
    return OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")


def _merge_question(question: str, extra_context: str | None = None) -> str:
    
    if extra_context:
        return f"{question}\n\nДополнительный контекст:\n{extra_context}"
    
    return question


async def ask_with_db(question: str, extra_context: str | None = None) -> str:
    client = _build_client()
    merged_question = _merge_question(question, extra_context)
    
    schema_text = await get_schema_text()
    raw = llm_make_sql(client, merged_question, schema_text)
    sql = extract_from_sql(raw)
    rows = await run_sql(sql)

    if rows and len(rows) == 1 and isinstance(rows[0], dict) and len(rows[0]) == 1:
        only_value = next(iter(rows[0].values()))
        if only_value is None:
            return "0"
        return str(only_value)

    return json.dumps(rows, ensure_ascii=False, indent=2)
    
async def main():
    q = "Сколько видео набрало больше 100 000 просмотров за всё время?"
    answer = await ask_with_db(q)
    print("\n=== FINAL ANSWER ===")
    print(answer)

if __name__ == '__main__':
    asyncio.run(main())

