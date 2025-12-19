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

# ------------------ NEWS API ------------------

def search_news(query: str) -> list:
    url = "https://newsapi.org/v2/everything"

    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
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

    articles = data.get("articles", [])

    results = []
    for a in articles:
        if a.get("title") and a.get("source", {}).get("name"):
            results.append(
                f"{a['source']['name']}: {a['title']}"
            )

    return results

# ------------------ HANDLERS ------------------

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🤖 TruthLens — проверка новостей\n\n"
        "Отправь новость или утверждение, и я определю:\n"
        "✅ РЕАЛ\n"
        "❌ ФЕЙК\n"
        "⚠️ НЕПОДТВЕРЖДЕНО\n\n"
        "Я использую актуальные данные из новостных СМИ."
    )

@dp.message()
async def analyze(message: Message):
    user_text = message.text

    articles = search_news(user_text)

    if articles:
        news_context = "Свежие заголовки СМИ:\n" + "\n".join(articles)
    else:
        news_context = (
            "Свежих подтверждений в новостных источниках не найдено."
        )

    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — сервис fact-checking.\n"
                    "Используй ТОЛЬКО предоставленные заголовки СМИ.\n\n"
                    "Правила:\n"
                    "- Если информация подтверждена СМИ — РЕАЛ.\n"
                    "- Если данных нет или они неполные — НЕПОДТВЕРЖДЕНО.\n"
                    "- Если информация явно противоречит фактам — ФЕЙК.\n\n"
                    "Формат ответа:\n"
                    "СТАТУС\n"
                    "Короткое объяснение (1–2 предложения).\n"
                    "Если есть источники — упомяни их."
                ),
            },
            {
                "role": "user",
                "content": f"Утверждение: {user_text}\n\n{news_context}",
            },
        ]
    )

    result = response.choices[0].message.content
    await message.answer(result)

# ------------------ START ------------------

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
