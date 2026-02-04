from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
import sys
import os
from aiogram.utils.markdown import html_decoration as hd
from user.kbs import main_kbs


user_router = Router()

@user_router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("👋 Привет! Я бот для комманды RTL.", reply_markup=main_kbs())

@user_router.callback_query(F.data == 'chat')
async def chat_realisation(call:CallbackQuery):
    pass


    