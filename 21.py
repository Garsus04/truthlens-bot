from mistralai import Mistral

import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.methods import DeleteWebhook
from aiogram.types import Message


api_key = "8YDHr4rB2PpfRSu0ZSwg8jFVBzmpI7RI" # API плюч MistalAI
model = "mistral-large-latest"

client = Mistral(api_key=api_key)

TOKEN = '8473697066:AAElW0-SW8x9fIqGAFT24FG1xf9iYqSkaIU' # ⁡⁢⁡⁢⁣⁣ПОМЕНЯЙТЕ ТОКЕН БОТА НА ВАШ⁡

logging.basicConfig(level=logging.INFO)
bot = Bot(TOKEN)
dp = Dispatcher()


# ⁡⁢⁣⁡⁢⁣⁣ОБРАБОТЧИК КОМАНДЫ СТАРТ⁡⁡
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer('Привет! Я бот с подключенной нейросетью, отправь свой запрос', parse_mode = 'HTML')


# ⁡⁢⁣⁣ОБРАБОТЧИК ЛЮБОГО ТЕКСТОВОГО СООБЩЕНИЯ⁡
@dp.message(lambda message: message.text)
async def filter_messages(message: Message):
    chat_response = client.chat.complete(
    model= model,
    messages = [
        {
            "role": "system",
            "content": "",
        },
        {
            "role": "user",
            "content": message.text,
        },
    ]
    )
    text = chat_response.choices[0].message.content
    await message.answer(text, parse_mode = "Markdown")


async def main():
    await bot(DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
