import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from huggingface_hub import AsyncInferenceClient

# Берем ключи из настроек сервера (Environment Variables)
TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
# Используем Qwen 2.5 Coder через API
MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"

bot = Bot(token=TOKEN)
dp = Dispatcher()
client = AsyncInferenceClient(model=MODEL_ID, token=HF_TOKEN)

# Список чатов, где бот активен
active_chats = set()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Я твой ИИ-двойник. Команды:\n/on — включить меня тут\n/off — выключить")

@dp.message(Command("on"))
async def on(message: types.Message):
    active_chats.add(message.chat.id)
    await message.answer("✅ Бот активен. Теперь я буду отвечать за тебя в этом чате.")

@dp.message(Command("off"))
async def off(message: types.Message):
    active_chats.discard(message.chat.id)
    await message.answer("❌ Бот выключен.")

@dp.message()
async def auto_reply(message: types.Message):
    # Отвечаем, только если бот включен и это не сообщение от другого бота
    if message.chat.id not in active_chats or message.from_user.is_bot:
        return

    # Эффект "печатает..."
    await bot.send_chat_action(message.chat.id, "typing")

    prompt = f"Ты — умный помощник и программист. Ответь на сообщение пользователя: {message.text}"
    
    try:
        # Запрос к ИИ (бесплатно)
        response = await client.text_generation(
            prompt, 
            max_new_tokens=500,
            temperature=0.7
        )
        await message.reply(response)
    except Exception as e:
        print(f"Error: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
