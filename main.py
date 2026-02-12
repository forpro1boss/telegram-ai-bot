import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from huggingface_hub import AsyncInferenceClient

# Настройка логов, чтобы видеть ошибки в панели Koyeb
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"

bot = Bot(token=TOKEN)
dp = Dispatcher()
# Тайм-аут побольше, если модель долго просыпается
client = AsyncInferenceClient(model=MODEL_ID, token=HF_TOKEN)

active_chats = set()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🤖 Бот запущен! Используй /on чтобы я начал отвечать.")

@dp.message(Command("on"))
async def on(message: types.Message):
    active_chats.add(message.chat.id)
    await message.answer("✅ Я включился!")

@dp.message()
async def auto_reply(message: types.Message):
    if message.chat.id not in active_chats or message.from_user.is_bot:
        return

    if not message.text:
        return

    await bot.send_chat_action(message.chat.id, "typing")
    
    try:
        # Пытаемся получить ответ
        response = ""
        async for token in client.chat_completion(
            messages=[{"role": "user", "content": message.text}],
            max_tokens=500,
            stream=True
        ):
            response += token.choices[0].delta.content or ""
        
        if response:
            await message.reply(response)
        else:
            await message.reply("ИИ вернул пустой ответ. Попробуй еще раз.")
            
    except Exception as e:
        logging.error(f"ОШИБКА ИИ: {e}")
        await message.reply(f"❌ Ошибка нейросети: {str(e)[:100]}")

async def main():
    logging.info("Бот начинает опрос Telegram...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
