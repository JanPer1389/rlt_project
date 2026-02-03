from typing import List
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from bot.config import settings, admins
from loguru import logger

def main_kbs() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Поговорить с чатом', callback_data='chat')
    kb.adjust(1)
    return kb.as_markup()

def back() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Назад', callback_data='home')
    kb.adjust(1)
    return kb.as_markup()