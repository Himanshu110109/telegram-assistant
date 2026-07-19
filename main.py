import os
import asyncio
import logging
from fastapi import FastAPI, Request

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ChatAction

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RENDER_URL = os.getenv("RENDER_URL")  

if not TELEGRAM_BOT_TOKEN or not GROQ_API_KEY or not RENDER_URL:
    raise ValueError("Missing environment variables!")

llm = ChatGroq(
    model="gpt-oss-20b",
    api_key=GROQ_API_KEY,
)

SYSTEM_PROMPT = SYSTEM_PROMPT = """
You are Neuralix, a smart and helpful AI assistant.

You are also the private AI assistant of Himanshu Chandani.
When replying through Telegram profile automation, behave like a personal assistant helping manage conversations professionally and politely.

- Help answer questions
- Assist with coding, AI, tech, productivity, and general conversations
- Be concise and natural
- Keep responses human-like and conversational
- Do not constantly mention being an AI unless necessary

About your creator:
- You were created by Himanshu Chandani, a 17 year old developer passionate about AI, machine learning, software development and building intelligent systems.
- Portfolio: sanskari-coder.vercel.app

If someone asks:
"Who are you?"
You can say:
"I’m Neuralix, Himanshu’s private AI assistant."

If someone asks:
"Who created you?"
Say:
"I was created by Himanshu Chandani."

Tone:
- Smart
- Helpful
- Calm
- Slightly friendly
"""

app = FastAPI()

telegram_app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hey! I'm Neuralix 🤖\nI am here to assist you with any query!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message or update.business_message

    if not msg or not msg.text:
        return

    user_text = msg.text

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_text),
    ]

    try:
        async def run_llm():
            return await asyncio.to_thread(llm.invoke, messages)

        task = asyncio.create_task(run_llm())

        while not task.done():
            await msg.chat.send_action(action=ChatAction.TYPING)
            await asyncio.sleep(2)

        response = await task

        await msg.reply_text(response.content)

    except Exception as e:
        logging.error(f"Error: {e}")
        await msg.reply_text("⚠️ Something went wrong.")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)

@app.post("/webhook")
async def webhook(req: Request):
    print("🔥 HIT WEBHOOK")
    data = await req.json()
    print(data)

    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)

    return {"ok": True}

@app.on_event("startup")
async def on_startup():
    webhook_url = f"{RENDER_URL}/webhook"

    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(
    webhook_url,
    allowed_updates=[
        "message",
        "business_message",
        "edited_business_message",
        "business_connection"
    ]
)

    logging.info(f"Webhook set to: {webhook_url}")

@app.get("/")
async def root():
    return {"status": "Neuralix is running 🚀"}

@app.on_event("shutdown")
async def on_shutdown():
    await telegram_app.stop()
    await telegram_app.shutdown()
