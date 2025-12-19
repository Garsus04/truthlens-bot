import asyncio
import logging
import os
import requests

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from mistralai import Mistral

# ------------------ НАСТРОЙКИ ------------------

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

client = Mistral(api_key=MISTRAL_API_KEY)

# ------------------ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ------------------

def is_simple_fact(text: str) -> bool:
    """
    Короткий общий факт, не новость
    """
    words = text.split()
    has_digits = any(char.isdigit() for char in text)
    return len(words) <= 4 and not has_digits


def looks_like_news(text: str) -> bool:
    """
    Похоже ли на новостное утверждение
    """
    keywords = [
        "reports", "said", "announced", "according",
        "today", "yesterday", "approved", "introduced",
        "bbc", "reuters", "cnn", "ap"
    ]
    text_lower = text.lower()
    return any(k in text_lower for k in keywords)


def search_news(query: str) -> list:
    url = "https://newsapi.org/v2/everything"

    params = {
        "q": query,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": 3,
        "apiKey": NEWS_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
    except Exception:
        return []

    if data.get("status") != "ok":
        return []

    return [
        f"{a['source']['name']}: {a['title']}"
        for a in data.get("articles", [])
        if a.get("title") and a.get("source", {}).get("name")
    ]

# ------------------ HANDLERS ------------------

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🤖 TruthLens — проверка новостей\n\n"
        "Я работаю в двух режимах:\n"
        "• Общие факты — отвечаю напрямую\n"
        "• Новостные утверждения — проверяю через СМИ\n\n"
        "Отправь текст для проверки."
    )


@dp.message()
async def analyze(message: Message):
    user_text = message.text.strip()

    # 🟢 ПРОСТОЙ ФАКТ → обычный ИИ
    if is_simple_fact(user_text):
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {
                    "role": "system",
                    "content": "Ответь кратко и по существу. Это общий факт.",
                },
                {
                    "role": "user",
                    "content": user_text,
                },
            ],
        )
        await message.answer(response.choices[0].message.content)
        return

    # 🟡 НЕ ПОХОЖЕ НА НОВОСТЬ → обычный ИИ
    if not looks_like_news(user_text):
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {
                    "role": "system",
                    "content": "Ответь логично и нейтрально.",
                },
                {
                    "role": "user",
                    "content": user_text,
                },
            ],
        )
        await message.answer(response.choices[0].message.content)
        return

    # 🔵 НОВОСТЬ → ПРОВЕРКА ЧЕРЕЗ NEWS API
    articles = search_news(user_text)

    if articles:
        context = "Подтверждённые заголовки СМИ:\n" + "\n".join(articles)
    else:
        context = "В новостных источниках подтверждений не найдено."

    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — сервис проверки новостей.\n"
                    "Если есть подтверждения в СМИ — РЕАЛ.\n"
                    "Если подтверждений нет — НЕПОДТВЕРЖДЕНО.\n\n"
                    "Формат:\n"
                    "СТАТУС\n"
                    "Короткое объяснение."
                ),
            },
            {
                "role": "user",
                "content": f"Утверждение: {user_text}\n\n{context}",
            },
        ],
    )

    await message.answer(response.choices[0].message.content)

# ------------------ START ------------------

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
