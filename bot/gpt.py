from openai import OpenAI
import os
from pathlib import Path
from dotenv import load_dotenv

def ask_with_reasoning(user_query: str, model: str = "deepseek/deepseek-v3.2") -> str:
    BASE_DIR = Path(__file__).parent.parent
    load_dotenv(dotenv_path=BASE_DIR/'.env')
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv('GPT_CREDENTIALS'),  
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": user_query
                }
            ],
            extra_body={"reasoning": {"enabled": True}}
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Ошибка: {e}"

ask = 'Есть ли вода на Марсе?'

print(ask_with_reasoning(ask))