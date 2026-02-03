from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
import sys
import os
from aiogram.utils.markdown import html_decoration as hd
from user.kbs import main_kbs


user_router = Router()

@user_router(CommandStart)
@user_router.callback_query(F.data == 'home')
async def cmd_start(message: Message, session_with_commit: AsyncSession):
    id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    await message.answer(
        text=f'Добро пожаловать {first_name} в бота для RTL-Company', reply_markup=main_kbs())

@user_router.callback_query(F.data == 'chat')
async def chat_realisation(call:CallbackQuery):
    pass


    