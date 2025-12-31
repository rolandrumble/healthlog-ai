"""
HealthLog AI - Telegram Bot
Allows users to log meals, symptoms, and medications via Telegram
"""

import os
import json
import asyncio
import httpx
import base64
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

load_dotenv()

# Bot token from BotFather
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Conversation states
WAITING_SYMPTOM, WAITING_SEVERITY, WAITING_MED_NAME, WAITING_MED_DOSAGE = range(4)

# User sessions (in production, use Redis or database)
user_sessions = {}

# =============================================================================
# Helper Functions
# =============================================================================

async def get_or_create_user(telegram_id: str, name: str) -> str:
    """Get existing user or create new one"""
    async with httpx.AsyncClient() as client:
        # Try to create user (will fail if exists, that's ok)
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/auth/signup",
                json={
                    "name": name,
                    "telegram_id": telegram_id
                }
            )
            if response.status_code == 200:
                return response.json().get("user_id")
        except:
            pass
    
    # Return telegram_id as user_id for simplicity
    return telegram_id

async def api_request(method: str, endpoint: str, **kwargs):
    """Make API request to backend"""
    async with httpx.AsyncClient() as client:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = await client.get(url, params=kwargs.get("params"))
        elif method == "POST":
            if "files" in kwargs:
                response = await client.post(url, files=kwargs["files"], data=kwargs.get("data"))
            else:
                response = await client.post(url, json=kwargs.get("json"), params=kwargs.get("params"))
        
        if response.status_code == 200:
            return response.json()
        return None

# =============================================================================
# Command Handlers
# =============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_id = await get_or_create_user(str(user.id), user.first_name)
    user_sessions[user.id] = {"user_id": user_id}
    
    welcome_message = f"""
🏥 *Welcome to HealthLog AI, {user.first_name}!*

I'm your personal health companion. Here's what I can do:

📸 *Log Meals* - Send me a photo of your food
📝 *Track Symptoms* - Use /symptom to log how you feel
💊 *Medications* - Use /meds to manage medications
📊 *Get Insights* - Use /report for your health summary
💬 *Chat* - Ask me health questions anytime!

*Quick Actions:*
• Send a 🍽️ *food photo* to log a meal
• Send a 🎤 *voice message* to log symptoms
• Type any health question to chat

Let's start your wellness journey! 🌟
"""
    
    keyboard = [
        ["📸 Log Meal", "📝 Log Symptom"],
        ["💊 Medications", "📊 My Report"],
        ["❓ Help"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        welcome_message,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
🆘 *HealthLog AI Help*

*Commands:*
/start - Start the bot
/symptom - Log a symptom
/meds - Manage medications
/report - Get weekly health report
/insights - Get AI health insights
/help - Show this help message

*Quick Actions:*
📸 Send a *photo* → Log a meal
🎤 Send *voice* → Transcribe symptoms
💬 Send *text* → Chat with AI assistant

*Tips:*
• Log meals consistently for better insights
• Rate symptom severity from 1-10
• Check your weekly report every Sunday

Need more help? Just ask me anything! 😊
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

# =============================================================================
# Meal Logging
# =============================================================================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages for meal logging"""
    user_id = str(update.effective_user.id)
    
    await update.message.reply_text("🔍 Analyzing your meal...")
    
    # Get the largest photo
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    
    # Download photo
    photo_bytes = await file.download_as_bytearray()
    
    # Send to API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/meals/log",
                files={"file": ("meal.jpg", bytes(photo_bytes), "image/jpeg")},
                data={
                    "user_id": user_id,
                    "meal_type": "snack",
                    "description": update.message.caption or ""
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                analysis = data.get("analysis", {})
                
                result_message = f"""
✅ *Meal Logged Successfully!*

🍽️ *{analysis.get('description', 'Meal')}*

📊 *Nutritional Estimate:*
• Calories: {analysis.get('calories', 'N/A')} kcal
• Protein: {analysis.get('protein', 'N/A')}g
• Carbs: {analysis.get('carbs', 'N/A')}g
• Fat: {analysis.get('fat', 'N/A')}g
• Fiber: {analysis.get('fiber', 'N/A')}g

⭐ Health Score: {analysis.get('health_score', 'N/A')}/10

💡 *Tip:* {analysis.get('suggestions', 'Keep up the good work!')}
"""
                await update.message.reply_text(result_message, parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ Sorry, I couldn't analyze that image. Please try again.")
    
    except Exception as e:
        print(f"Error processing meal: {e}")
        await update.message.reply_text("❌ Something went wrong. Please try again later.")

# =============================================================================
# Symptom Logging
# =============================================================================

async def symptom_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start symptom logging conversation"""
    await update.message.reply_text(
        "📝 *Log a Symptom*\n\nWhat symptom are you experiencing?\n\n_Example: headache, fatigue, nausea_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return WAITING_SYMPTOM

async def symptom_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive symptom name"""
    context.user_data['symptom'] = update.message.text
    
    keyboard = [[str(i) for i in range(1, 6)], [str(i) for i in range(6, 11)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        f"Got it: *{update.message.text}*\n\nHow severe is it? (1 = mild, 10 = severe)",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    return WAITING_SEVERITY

async def symptom_severity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive symptom severity and save"""
    try:
        severity = int(update.message.text)
        if not 1 <= severity <= 10:
            raise ValueError()
    except:
        await update.message.reply_text("Please enter a number between 1 and 10.")
        return WAITING_SEVERITY
    
    user_id = str(update.effective_user.id)
    symptom = context.user_data.get('symptom', 'Unknown')
    
    # Save to API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/symptoms/log",
                json={"symptom": symptom, "severity": severity},
                params={"user_id": user_id}
            )
            
            if response.status_code == 200:
                severity_emoji = "🟢" if severity <= 3 else "🟡" if severity <= 6 else "🔴"
                
                await update.message.reply_text(
                    f"""
✅ *Symptom Logged*

{severity_emoji} *{symptom}*
Severity: {severity}/10
Time: {datetime.now().strftime('%I:%M %p')}

_Track patterns with /insights_
""",
                    parse_mode="Markdown",
                    reply_markup=get_main_keyboard()
                )
    except Exception as e:
        print(f"Error logging symptom: {e}")
        await update.message.reply_text("❌ Couldn't save symptom. Please try again.")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current conversation"""
    await update.message.reply_text(
        "Cancelled. What would you like to do?",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

# =============================================================================
# Medication Management
# =============================================================================

async def meds_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show medication menu"""
    keyboard = [
        [InlineKeyboardButton("➕ Add Medication", callback_data="med_add")],
        [InlineKeyboardButton("📋 My Medications", callback_data="med_list")],
        [InlineKeyboardButton("✅ Log Taken", callback_data="med_take")],
        [InlineKeyboardButton("📊 Adherence Stats", callback_data="med_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "💊 *Medication Management*\n\nWhat would you like to do?",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def med_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle medication button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    action = query.data
    
    if action == "med_list":
        # Get medications from API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/api/medications/{user_id}")
                if response.status_code == 200:
                    meds = response.json().get("medications", [])
                    
                    if not meds:
                        await query.edit_message_text("No medications added yet. Use ➕ Add Medication to start.")
                        return
                    
                    med_text = "💊 *Your Medications:*\n\n"
                    for med in meds:
                        med_text += f"• *{med['name']}* - {med['dosage']}\n  _{med['frequency']}_\n\n"
                    
                    await query.edit_message_text(med_text, parse_mode="Markdown")
        except:
            await query.edit_message_text("❌ Couldn't fetch medications.")
    
    elif action == "med_stats":
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/api/medications/{user_id}/adherence")
                if response.status_code == 200:
                    stats = response.json()
                    
                    rate = stats.get("adherence_rate", 0)
                    emoji = "🌟" if rate >= 90 else "👍" if rate >= 70 else "💪"
                    
                    stats_text = f"""
📊 *Medication Adherence*

{emoji} *{rate}%* adherence rate

• Total scheduled: {stats.get('total_scheduled', 0)}
• Taken: {stats.get('taken', 0)} ✅
• Skipped: {stats.get('skipped', 0)} ❌

_Last {stats.get('period_days', 30)} days_
"""
                    await query.edit_message_text(stats_text, parse_mode="Markdown")
        except:
            await query.edit_message_text("❌ Couldn't fetch stats.")

# =============================================================================
# Reports & Insights
# =============================================================================

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate weekly health report"""
    user_id = str(update.effective_user.id)
    
    await update.message.reply_text("📊 Generating your health report...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/report/{user_id}")
            
            if response.status_code == 200:
                report = response.json()
                summary = report.get("summary", {})
                
                report_text = f"""
📊 *Weekly Health Report*
_{report.get('period', 'Last 7 days')}_

👤 *{report.get('user_name', 'User')}*

📈 *Summary:*
• Meals logged: {summary.get('meals_logged', 0)}
• Avg daily calories: {summary.get('avg_daily_calories', 'N/A')}
• Symptoms logged: {summary.get('symptoms_logged', 0)}
• Avg energy: {summary.get('avg_energy', 'N/A')}/10
• Avg mood: {summary.get('avg_mood', 'N/A')}/10

🍎 *Nutrition Averages:*
• Protein: {summary.get('nutrition_summary', {}).get('avg_daily_protein', 'N/A')}g
• Carbs: {summary.get('nutrition_summary', {}).get('avg_daily_carbs', 'N/A')}g
• Fat: {summary.get('nutrition_summary', {}).get('avg_daily_fat', 'N/A')}g

💡 *Recommendations:*
"""
                for rec in report.get('recommendations', []):
                    report_text += f"• {rec}\n"
                
                await update.message.reply_text(report_text, parse_mode="Markdown")
    except Exception as e:
        print(f"Error generating report: {e}")
        await update.message.reply_text("❌ Couldn't generate report. Please try again.")

async def insights_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get AI health insights"""
    user_id = str(update.effective_user.id)
    
    await update.message.reply_text("🧠 Analyzing your health patterns...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/symptoms/{user_id}/analysis")
            
            if response.status_code == 200:
                data = response.json()
                await update.message.reply_text(
                    f"🧠 *Health Insights*\n\n{data.get('analysis', 'No insights available yet.')}",
                    parse_mode="Markdown"
                )
    except:
        await update.message.reply_text("❌ Couldn't fetch insights.")

# =============================================================================
# Chat Handler
# =============================================================================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle general text messages as chat"""
    user_id = str(update.effective_user.id)
    message = update.message.text
    
    # Check for menu buttons
    if message == "📸 Log Meal":
        await update.message.reply_text("📸 Send me a photo of your meal!")
        return
    elif message == "📝 Log Symptom":
        return await symptom_start(update, context)
    elif message == "💊 Medications":
        return await meds_command(update, context)
    elif message == "📊 My Report":
        return await report_command(update, context)
    elif message == "❓ Help":
        return await help_command(update, context)
    
    # Otherwise, chat with AI
    await update.message.reply_chat_action("typing")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/chat",
                json={"message": message, "user_id": user_id},
                timeout=30.0
            )
            
            if response.status_code == 200:
                ai_response = response.json().get("response", "I'm not sure how to respond to that.")
                await update.message.reply_text(ai_response)
            else:
                await update.message.reply_text("🤔 I'm having trouble understanding. Try asking differently!")
    except:
        await update.message.reply_text("❌ Connection error. Please try again.")

# =============================================================================
# Voice Message Handler
# =============================================================================

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages - transcribe and log as symptom note"""
    await update.message.reply_text("🎤 Voice logging coming soon! For now, please type your symptoms.")

# =============================================================================
# Helper Functions
# =============================================================================

def get_main_keyboard():
    """Get main menu keyboard"""
    keyboard = [
        ["📸 Log Meal", "📝 Log Symptom"],
        ["💊 Medications", "📊 My Report"],
        ["❓ Help"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# =============================================================================
# Main Bot Setup
# =============================================================================

def main():
    """Start the bot"""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set!")
        print("Get a token from @BotFather on Telegram and add it to .env")
        return
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Conversation handler for symptoms
    symptom_conv = ConversationHandler(
        entry_points=[
            CommandHandler("symptom", symptom_start),
            MessageHandler(filters.Regex("^📝 Log Symptom$"), symptom_start)
        ],
        states={
            WAITING_SYMPTOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, symptom_name)],
            WAITING_SEVERITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, symptom_severity)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("meds", meds_command))
    application.add_handler(CommandHandler("report", report_command))
    application.add_handler(CommandHandler("insights", insights_command))
    application.add_handler(symptom_conv)
    application.add_handler(CallbackQueryHandler(med_callback, pattern="^med_"))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Start polling
    print("🤖 HealthLog AI Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
