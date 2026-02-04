import asyncio
from aiogram.types import BotCommand, BotCommandScopeDefault
from loguru import logger
from user.user_router import user_router
from config import bot, dp
from dao.database_middleware import DatabaseMiddlewareWithCommit, DatabaseMiddlewareWithoutCommit
import sys
from pathlib import Path
import os
sys.path.append(str(Path(__file__).parent.parent))


BASE_DIR = Path(__file__).parent.parent

ENV_PATH = BASE_DIR/'.env'

async def start_bot():
    try:
        id = os.getenv('MY_ID')
        await bot.send_message(chat_id=id,
                               text='Я запущен')
        logger.info('Бот запущен')
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

async def stop_bot():
    try:
        await bot.send_message(text = 'Я умер')
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
    
    logger.info('Бот остановлен')
    
    

async def main():
    dp.update.middleware.register(DatabaseMiddlewareWithCommit())
    dp.update.middleware.register(DatabaseMiddlewareWithoutCommit())
    dp.include_router(user_router)
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__=='__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Принудительное завршение работы через конструкцию Ctrl + C')
    finally:
        logger.info('Бот полностью остановлен')