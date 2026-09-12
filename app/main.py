import asyncio, logging, os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher
from .config import settings
from .db import SessionLocal
from .handlers import router
from .services import generate_future_lessons

async def generate():
    async with SessionLocal() as db: await generate_future_lessons(db)

async def main():
    os.makedirs('data',exist_ok=True)
    if not settings.bot_token or not settings.admin_telegram_id: raise RuntimeError('BOT_TOKEN and ADMIN_TELEGRAM_ID are required')
    logging.basicConfig(level=getattr(logging,settings.log_level.upper(),logging.INFO),format='%(asctime)s %(levelname)s %(name)s %(message)s')
    bot=Bot(settings.bot_token); dp=Dispatcher(); dp.include_router(router)
    await generate()
    scheduler=AsyncIOScheduler(timezone=settings.timezone); scheduler.add_job(generate,'interval',hours=6); scheduler.start()
    try: await dp.start_polling(bot)
    finally: scheduler.shutdown(); await bot.session.close()

if __name__=='__main__': asyncio.run(main())
