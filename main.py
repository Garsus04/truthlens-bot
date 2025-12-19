import asyncio
import logging
import os
import requests

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from mistralai import Mistral

# ---------------- НАСТРОЙКИ ----------------

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = Mistral(api_key=MISTRAL_API_KEY)

# ---------------- ЛОГИКА КЛАССИФИКАЦИИ ----------------

def is_simple_fact(text: str) -> bool:
    words = text.split()
    has_digits = any(c.isdigit() for c in text)
    return len(words) <= 4 and not has_digits

def is_general_claim(text: str) -> bool:
    vague_words = [
        "планируют", "обсуждают", "хотят",
        "ожидается", "возможно", "рассматривают"
    ]
    t = text.lower()
    return any(w in t for w in vague_words)

def looks_like_news(text: str) -> bool:
    keywords = [
        "reports", "reported", "said", "announced",
        "today", "yesterday", "approved", "introduced",
        "bbc", "reuters", "cnn", "ap"
    ]
    t = text.lower()
    return any(k in t for k in keywords)

# ---------------- NEWS API ----------------

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
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
    except Exception:
        return []

    if data.get("status") != "ok":
        return []

    return [
        f"{a['source']['name']}: {a['title']}"
        for a in data.get("articles", [])
        if a.get("title") and a.get("source", {}).get("name")
    ]

# ---------------- HANDLERS ----------------

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🤖 TruthLens — фактчекинг новостей\n\n"
        "Как я работаю:\n"
        "• Простые факты — отвечаю напрямую\n"
        "• Общие утверждения — НЕПОДТВЕРЖДЕНО\n"
        "• Новостные сообщения — проверяю через СМИ\n\n"
        "Отправь сообщение для проверки."
    )

@dp.message()
async def analyze(message: Message):
    text = message.text.strip()

    # 🟢 ПРОСТОЙ ФАКТ
    if is_simple_fact(text):
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {"role": "system", "content": "Ответь кратко и точно. Это общеизвестный факт."},
                {"role": "user", "content": text},
            ],
        )
        await message.answer(response.choices[0].message.content)
        return

    # 🟡 ОБЩЕЕ УТВЕРЖДЕНИЕ
    if is_general_claim(text):
        await message.answer(
            "СТАТУС: НЕПОДТВЕРЖДЕНО\n"
            "Утверждение сформулировано в общем виде и не содержит "
            "конкретных подтверждений в новостных источниках."
        )
        return

    # 🔵 НОВОСТЬ
    if looks_like_news(text):
        articles = search_news(text)

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
                    "content": f"Утверждение: {text}\n\n{context}",
                },
            ],
        )
        await message.answer(response.choices[0].message.content)
        return

    # ⚪ ВСЁ ОСТАЛЬНОЕ
    await message.answer(
        "СТАТУС: НЕПОДТВЕРЖДЕНО\n"
        "Информация не относится к конкретному новостному событию "
        "и не имеет подтверждений в СМИ."
    )

# ---------------- START ----------------

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
