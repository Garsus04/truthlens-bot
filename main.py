
import os
print("DEBUG BOT_TOKEN:", os.getenv("BOT_TOKEN"))
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

from mistralai import Mistral
import os

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

@dp.message()
async def analyze(message: Message):
    user_text = message.text

    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — ИИ для проверки новостей. "
                    "Определи, является ли текст фейковой новостью или реальной. "
                    "Ответь кратко: ФЕЙК или РЕАЛ, и дай короткое объяснение."
                ),
            },
            {
                "role": "user",
                "content": user_text,
            },
        ]
    )

    result = response.choices[0].message.content
    await message.answer(result)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())



