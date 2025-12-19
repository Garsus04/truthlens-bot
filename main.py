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

# ---------------- КЛАССИФИКАЦИЯ ЗАПРОСОВ ----------------

def is_simple_fact(text: str) -> bool:
    t = text.lower()
    words = t.split()

    # короткие справочные фразы
    if len(words) <= 6:
        return True

    # год / текущее время
    if any(w in t for w in ["год", "сейчас", "ща", "сегодня"]):
        return True

    # титулы / награды
    if any(w in t for w in ["игра года", "goty", "game of the year"]):
        return True

    return False


def is_general_claim(text: str) -> bool:
    vague = [
        "планируют", "обсуждают", "хотят",
        "ожидается", "возможно", "рассматривают",
        "может", "вероятно"
    ]
    t = text.lower()
    return any(v in t for v in vague)


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
        "🤖 TruthLens — проверка информации\n\n"
        "Я умею:\n"
        "• отвечать на простые факты\n"
        "• определять фейки и слухи\n"
        "• проверять новости через СМИ\n\n"
        "Напиши сообщение."
    )

@dp.message()
async def analyze(message: Message):
    text = message.text.strip()

    # 🟢 ПРОСТОЙ ФАКТ → обычный ИИ
    if is_simple_fact(text):
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {
                    "role": "system",
                    "content": "Ответь кратко, по-человечески и без статусов.",
                },
                {
                    "role": "user",
                    "content": text,
                },
            ],
        )
        await message.answer(response.choices[0].message.content)
        return

    # 🟡 ОБЩЕЕ УТВЕРЖДЕНИЕ → НЕПОДТВЕРЖДЕНО
    if is_general_claim(text):
        await message.answer(
            "СТАТУС: НЕПОДТВЕРЖДЕНО\n"
            "Это общее утверждение без конкретных фактов "
            "или подтверждённых источников."
        )
        return

    # 🔵 НОВОСТЬ → ПРОВЕРКА ЧЕРЕЗ СМИ
    if looks_like_news(text):
        articles = search_news(text)

        if articles:
            context = "Источники СМИ:\n" + "\n".join(articles)
            status = "СТАТУС: РЕАЛ"
        else:
            context = "Подтверждений в надёжных СМИ не найдено."
            status = "СТАТУС: НЕПОДТВЕРЖДЕНО"

        response = client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — сервис фактчекинга.\n"
                        "Сначала выдай статус, затем короткое объяснение."
                    ),
                },
                {
                    "role": "user",
                    "content": f"{status}\n\nУтверждение: {text}\n\n{context}",
                },
            ],
        )
        await message.answer(response.choices[0].message.content)
        return

    # ⚪ ВСЁ ОСТАЛЬНОЕ → ОСМЫСЛЕННЫЙ ФЕЙК
    await message.answer(
        "СТАТУС: НЕПОДТВЕРЖДЕНО\n"
        "Информация не имеет признаков достоверного "
        "новостного сообщения и не подтверждена фактами."
    )

# ---------------- START ----------------

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
