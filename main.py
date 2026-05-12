import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import os

# ── Config ────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("8645966729:AAHOhkMYH_J8UjMKOKeHGIcCaaafgoUgsD0", "")

# ── Logger (module-level, not inside main) ────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ── Handler stubs (replace with your real implementations) ─
async def start_command(update: Update, context) -> None:
    await update.message.reply_text("Welcome!")

async def join_command(update: Update, context) -> None:
    await update.message.reply_text("Join command!")

async def help_command(update: Update, context) -> None:
    await update.message.reply_text("Help!")

async def about_command(update: Update, context) -> None:
    await update.message.reply_text("About!")

async def button_callback(update: Update, context) -> None:
    query = update.callback_query
    await query.answer()

async def handle_message(update: Update, context) -> None:
    await update.message.reply_text(update.message.text)


# ── Main ──────────────────────────────────────────────────
def main() -> None:
    """Run the bot."""

    if not TELEGRAM_BOT_TOKEN:
        logger.error("Bot token is missing!")
        return

    try:
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Commands
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("join", join_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))

        # Buttons
        application.add_handler(CallbackQueryHandler(button_callback))

        # Messages
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        )

        logger.info("Bot started successfully!")

        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )

    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise  # re-raise so the error is visible, not silently swallowed


if __name__ == "__main__":
    main()    query = update.callback_query
    await query.answer()

async def handle_message(update: Update, context) -> None:
    await update.message.reply_text(update.message.text)


# ── Main ──────────────────────────────────────────────────
def main() -> None:
    """Run the bot."""

    if not TELEGRAM_BOT_TOKEN:
        logger.error("Bot token is missing!")
        return

    try:
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Commands
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("join", join_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))

        # Buttons
        application.add_handler(CallbackQueryHandler(button_callback))

        # Messages
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        )

        logger.info("Bot started successfully!")

        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )

    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise  # re-raise so the error is visible, not silently swallowed


if __name__ == "__main__":
    main()
