import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ============================================================
# CONFIGURATION
# ============================================================
TELEGRAM_TOKEN = "8945041907:AAE21dCFHV9IglqRiFlalN8zvVzDFo5DYHw"
GEMINI_API_KEY = "AQ.Ab8RN6Kt_KyGRkYo0_bGaqiVUFRCIrxOPoeizlnCXijHbA8fVA"

# Special users jab message karein toh special reply
SPECIAL_USERS = ["koivad niranidhoo", "jabi mirabot"]
SPECIAL_REPLY = "Hello! 👋 Mujhe Satyam ne banaya hai, main Satyam ka AI Assistant Bot hun! 🤖\n\nAap mujhse kuch bhi puch sakte hain!"

# ============================================================
# SETUP
# ============================================================
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Store chat history
chat_histories = {}

# ============================================================
# COMMANDS
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hello {user_name}! 👋\n\n"
        f"Main Satyam ka AI Assistant Bot hun! 🤖\n"
        f"Mujhe Satyam ne banaya hai.\n\n"
        f"Aap mujhse kuch bhi puch sakte hain:\n"
        f"💬 Normal baatein\n"
        f"❓ Sawaal jawab\n"
        f"📝 Writing help\n"
        f"🧮 Math problems\n"
        f"🌐 Koi bhi topic!\n\n"
        f"Type karo aur baat karo! 😊"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Satyam AI Bot - Help*\n\n"
        "/start - Bot shuru karo\n"
        "/help - Help dekho\n"
        "/clear - Chat history clear karo\n\n"
        "Bas message karo, main reply dunga! 😊",
        parse_mode='Markdown'
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in chat_histories:
        del chat_histories[user_id]
    await update.message.reply_text("✅ Chat history clear ho gayi! Naya conversation shuru karo.")

# ============================================================
# MESSAGE HANDLER
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_name = user.first_name.lower() if user.first_name else ""
    user_id = user.id
    message_text = update.message.text

    # Check karo special users hain ya nahi
    for special_user in SPECIAL_USERS:
        if special_user.lower() in user_name:
            await update.message.reply_text(SPECIAL_REPLY)
            return

    # Typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Chat history maintain karo
        if user_id not in chat_histories:
            chat_histories[user_id] = []

        # System prompt
        system_prompt = """Tu Satyam ka AI Assistant Bot hai. 
        Tujhe Satyam ne banaya hai. 
        Tu helpful, friendly aur smart hai.
        Hinglish (Hindi + English mix) mein baat kar jab user Hinglish mein bole.
        English mein baat kar jab user English mein bole.
        Short aur clear replies de."""

        # Full conversation build karo
        full_prompt = system_prompt + "\n\nConversation:\n"
        for msg in chat_histories[user_id][-10:]:  # Last 10 messages
            full_prompt += f"{msg['role']}: {msg['content']}\n"
        full_prompt += f"User: {message_text}\nAssistant:"

        # Gemini se reply lo
        response = model.generate_content(full_prompt)
        reply = response.text

        # History update karo
        chat_histories[user_id].append({"role": "User", "content": message_text})
        chat_histories[user_id].append({"role": "Assistant", "content": reply})

        # Reply bhejo
        await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Kuch error aa gaya, thodi der baad try karo!")

# ============================================================
# PHOTO HANDLER
# ============================================================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        file_bytes = await file.download_as_bytearray()

        caption = update.message.caption or "Is image ke baare mein batao"

        image_parts = [{"mime_type": "image/jpeg", "data": bytes(file_bytes)}]
        vision_model = genai.GenerativeModel('gemini-1.5-flash')
        response = vision_model.generate_content([caption, image_parts[0]])

        await update.message.reply_text(f"🖼️ *Image Analysis:*\n\n{response.text}", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Photo error: {e}")
        await update.message.reply_text("❌ Image process nahi ho saki!")

# ============================================================
# MAIN
# ============================================================
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Satyam AI Bot chal raha hai...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
