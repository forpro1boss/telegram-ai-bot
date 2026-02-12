import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from huggingface_hub import AsyncInferenceClient
from aiohttp import web  # Это для обмана Koyeb

# Настройка логов
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"

bot = Bot(token=TOKEN)
dp = Dispatcher()
client = AsyncInferenceClient(model=MODEL_ID, token=HF_TOKEN)

active_chats = set()

# --- ХАК ДЛЯ KOYEB: Фейковый веб-сервер ---
async def handle_koyeb(request):
    return web.Response(text="Бот живой и работает!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_koyeb)
    runner = web.AppRunner(app)
    await runner.setup()
    # Koyeb сам скажет, на каком порту нам "притвориться" сайтом
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Фейковый сервер запущен на порту {port}")

# --- ЛОГИКА БОТА ---
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🤖 Бот-двойник запущен!\n/on — включить здесь\n/off — выключить")

@dp.message(Command("on"))
async def on(message: types.Message):
    active_chats.add(message.chat.id)
    await message.answer("✅ Теперь я отвечаю за тебя в этом чате.")

@dp.message()
async def auto_reply(message: types.Message):
    if message.chat.id not in active_chats or message.from_user.is_bot or not message.text:
        return

    await bot.send_chat_action(message.chat.id, "typing")
    
    try:
        response = ""
        # Используем chat_completion для Qwen
        async for token in client.chat_completion(
            messages=[{"role": "user", "content": message.text}],
            max_tokens=500,
            stream=True
        ):
            response += token.choices[0].delta.content or ""
        
        if response:
            await message.answer(response)
    except Exception as e:
        logging.error(f"Ошибка ИИ: {e}")

# --- ЗАПУСК ВСЕГО ВМЕСТЕ ---
async def main():
    # Запускаем и фейковый сервер, и бота одновременно
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
