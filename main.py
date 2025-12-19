import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("🤖 Бот работает на Railway!")

@dp.message()
async def echo(message: Message):
    await message.answer("Сообщение получено 👍")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

