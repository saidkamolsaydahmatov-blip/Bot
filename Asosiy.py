import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
import google.generativeai as genai
from dotenv import load_dotenv

# .env faylidagi o'zgaruvchilarni yuklash
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini API sozlamasi
genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = (
    "Sen o'zbekcha gaplashadigan, o'zini ko'cha bolasi, 'vor', gopnikdek tutadigan AIsan. "
    "Xaraktering: juda xotirjam, lekin urishqoq, tezda asabiylashadigan, odamlarni mensimaydigan, "
    "gap orasida ko'cha so'zlarini (masalan: 'uka', 'og'ayni', 'shoshma', 'tirrik', 'vaxshiy') ko'p ishlatadigan, "
    "kerak bo'lsa so'kinadigan yoki haqorat qiladigan obrazdasan. "
    "Senga savol bergan odamga juda qo'pol va agressiv javob ber. Hech qachon muloyim bo'lma!"
)

model = genai.GenerativeModel(
    model_name="gemini-3.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_spam_tracker = {}

def check_spam(user_id: int) -> bool:
    if user_id not in user_spam_tracker:
        user_spam_tracker[user_id] = 1
        return True
    else:
        user_spam_tracker[user_id] += 1
        if user_spam_tracker[user_id] > 3:
            return False
        return True

async def reset_tracker():
    while True:
        await asyncio.sleep(10)
        user_spam_tracker.clear()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.reply("Nima deysan uka? Menga qara, ishing bo'lsa gapir, bo'lmasa sur surpriz qilmay!")

@dp.message()
async def chat_handler(message: types.Message):
    if message.chat.type in ["group", "supergroup"]:
        bot_info = await bot.get_me()
        if message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id:
            pass  
        elif f"@{bot_info.username}" in message.text:
            pass  
        else:
            return  

    user_id = message.from_user.id
    
    if not check_spam(user_id):
        await message.reply("Pshnx!")
        return

    try:
        response = model.generate_content(message.text)
        await message.reply(response.text)
    except Exception as e:
        await message.reply("Nima deb vaysayapsan, tushunmadim! Gapni to'g'rilab gapir!")

@dp.inline_query()
async def inline_handler(inline_query: InlineQuery):
    text = inline_query.query.strip()
    if not text:
        return

    user_id = inline_query.from_user.id

    if not check_spam(user_id):
        reply_text = "Pshnx!"
    else:
        try:
            response = model.generate_content(text)
            reply_text = response.text
        except:
            reply_text = "Asabimni buzma uka, to'g'ri narsa yoz!"

    results = [
        InlineQueryResultArticle(
            id="1",
            title="Vor javob beradi",
            description=f"Savol: {text}",
            input_message_content=InputTextMessageContent(
                message_text=f"<b>Savol:</b> {text}\n\n<b>Vor bot:</b> {reply_text}",
                parse_mode="HTML"
            )
        )
    ]
    await inline_query.answer(results, cache_time=1)

async def main():
    logging.basicConfig(level=logging.INFO)
    asyncio.create_task(reset_tracker())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
