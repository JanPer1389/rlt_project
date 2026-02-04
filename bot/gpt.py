import asyncio
import asyncpg
import re
from config import database_url
from pydantic import BaseModel, Field, field_validator
from openai import OpenAI
from pathlib import Path
import os
from dotenv import load_dotenv
import json




def to_asyncpg_dsn(url: str)->str:
    return url.replace('postgresql+asyncpg://', 'postgresql://',1)

FORBIDDEN = re.compile(r"\b(drop|delete|update|insert|alter|truncate|create|grant|revoke|copy)\b", re.IGNORECASE)


class RunSQLInput(BaseModel):
    sql: str = Field(..., min_length=1, max_length=5000)
    
    @field_validator('sql')
    @classmethod
    def validate_and_normalize_sql(cls, v:str) -> str:
        s = v.strip()
        
        if ';' in s:
            raise ValueError('Никаких ;')
        if not s.lower().startswith('select'):
            raise ValueError('Разрешены только SELECT')
        if FORBIDDEN.search(s):
            raise ValueError('Запрещены все опасные команды SQL')
        if re.search(r'\blimit\b', s, re.IGNORECASE) is None:
            s += ' LIMIT 50'
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
        tables.setdefault(r['table_name'], []).append(f'{r['column_name']} {r['data_type']}')
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
        "- Верни СТРОГО JSON без лишнего текста: {\"sql\": \"...\"}\n"
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

def extract_from_sql(text:str)->str:
    data = json.loads(text)
    return data['sql']

async def ask_db(question: str)->str:
    BASE_DIR = Path(__file__).parent.parent
    ENV_PATH = BASE_DIR / ".env"
    load_dotenv(ENV_PATH)

    api_key = os.getenv("GPT_CREDENTIALS")
    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    
    schema_text = await get_schema_text()
    print("=== SCHEMA (коротко) ===")
    print(schema_text.splitlines()[:4], "...", sep="\n")
    
    raw = llm_make_sql(client, question, schema_text)
    print("\n=== LLM RAW ANSWER ===")
    print(raw)
    sql = extract_from_sql(raw)
    print("\n=== SQL TO EXECUTE ===")
    print(sql)
    rows = await run_sql(sql)
    if rows and 'cnt' in rows[0] and len(rows[0]) == 1:
        return str(rows[0]['cnt'])
    return json.dumps(rows, ensure_ascii=False, indent=2)
    
    
async def main():
    q = "Сколько видео набрало больше 100 000 просмотров за всё время?"
    answer = await ask_db(q)
    print("\n=== FINAL ANSWER ===")
    print(answer)

if __name__ == '__main__':
    asyncio.run(main())

