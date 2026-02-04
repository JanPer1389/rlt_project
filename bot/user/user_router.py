from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import html_decoration as hd
from user.kbs import main_kbs
from gpt import ask_with_db
from user.kbs import main_kbs
from user.schemas import DBQuestion

user_router = Router()

@user_router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    headline = hd.bold("🤖 RTL Data-GPT")
    description = (
        "Я подключён к вашей Postgres базе и умею отвечать на вопросы по данным.\n"
        "Нажмите кнопку «Чат», или напишите запрос в формате: \n"
        f"{hd.code('/db Покажи топ-5 видео по просмотрам')}"
    )
    await message.answer(f"{headline}\n\n{description}", reply_markup=main_kbs())

@user_router.callback_query(F.data == 'chat')
async def chat_realisation(call: CallbackQuery) -> None:
    await call.message.answer(
        "💬 Напишите вопрос к базе. Например:\n"
        f"{hd.code('/db Сколько всего пользователей?')}"
    )
    await call.answer()


@user_router.message(F.text.startswith('/db'))
async def db_question(message: Message) -> None:
    user_query = message.text.removeprefix('/db').strip()
    if not user_query:
        await message.answer("⚠️ Добавьте вопрос после команды /db.")
        return

    status_message = await message.answer("🧠 Думаю и обращаюсь к базе данных...")

    try:
        parsed = DBQuestion(question=user_query)
        extra_context = None
        if parsed.date_range:
            extra_context = (
                f"Диапазон дат: {parsed.date_range.start_date} - "
                f"{parsed.date_range.end_date} (включительно)."
            )

    
        answer = await ask_with_db(parsed.normalized_question, extra_context=extra_context)
        response = (
            f"{hd.bold('✅ Ответ от Data-GPT')}\n\n"
            f"{hd.italic('Запрос:')} {hd.code(parsed.normalized_question)}\n\n"
            f"{answer}"
        )
        await status_message.edit_text(response)
    except Exception as exc:
        await status_message.edit_text(
            f"{hd.bold('🚨 Ошибка при запросе')}\n{hd.code(str(exc))}"
        )