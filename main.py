import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from mistralai import Mistral

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

client = Mistral(api_key=MISTRAL_API_KEY)


@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🤖 TruthLens\n\n"
        "Отправь текст новости, и я проверю:\n"
        "РЕАЛ / ФЕЙК / НЕПОДТВЕРЖДЕНО"
    )


@dp.message()
async def analyze(message: Message):
    user_text = message.text

    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — ИИ-сервис для проверки новостей (fact-checking). "
                    "Проанализируй текст и отнеси его строго к ОДНОЙ категории:\n"
                    "1) РЕАЛ — подтверждено официальными источниками\n"
                    "2) ФЕЙК — ложная или вымышленная информация\n"
                    "3) НЕПОДТВЕРЖДЕНО — нет официального подтверждения или это предположение\n\n"
                    "Формат ответа:\n"
                    "СТАТУС (РЕАЛ / ФЕЙК / НЕПОДТВЕРЖДЕНО)\n"
                    "Короткое объяснение (1–3 предложения).\n"
                    "Не выдумывай факты и не утверждай, если нет подтверждения."
                )
            },
            {
                "role": "user",
                "content": user_text
            }
        ]
    )

    result = response.choices[0].message.content
    await message.answer(result)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
