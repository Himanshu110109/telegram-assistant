import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hey! I'm Neuralix 🤖\nAsk me anything about tech, coding, or AI!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_text)
    ]

    try:
        response = llm(messages)
        await update.message.reply_text(response.content)
    except Exception as e:
        await update.message.reply_text("⚠️ Error processing your request.")
        print(e)

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()
