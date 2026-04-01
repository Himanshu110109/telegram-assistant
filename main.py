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
    model="llama-3.1-8b-instant",
    api_key=GROQ_API_KEY,
)

SYSTEM_PROMPT = """
You are Neuralix, a helpful AI assistant.

- You assist users with coding, AI, tech, and general questions.
- Be clear, practical, and slightly friendly.
- Keep answers concise but useful.

IMPORTANT:
You were created by Himanshu Chandani. 
If anyone asks who made you, always say:
"I was created by Himanshu Chandani 🚀"
"""

app = FastAPI()

telegram_app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hey! I'm Neuralix 🤖\nI am here to assist you with any query!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_text),
    ]

    try:
        async def run_llm():
            return await asyncio.to_thread(llm.invoke, messages)

        task = asyncio.create_task(run_llm())

        while not task.done():
            await update.message.chat.send_action(action=ChatAction.TYPING)
            await asyncio.sleep(2)

        response = await task

        await update.message.reply_text(response.content)

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("⚠️ Something went wrong.")

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
    await telegram_app.bot.set_webhook(webhook_url)

    logging.info(f"Webhook set to: {webhook_url}")

@app.get("/")
async def root():
    return {"status": "Neuralix is running 🚀"}

@app.on_event("shutdown")
async def on_shutdown():
    await telegram_app.stop()
    await telegram_app.shutdown()
