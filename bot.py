#!/usr/bin/env python3
"""
Free Ethio Server - SlipNet VPN Config Generator Telegram Bot
Generates slipnet:// URIs for UK and Germany servers using SSH credentials from hackkcah.com
"""

import os
import sys
import logging
import base64
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from telegram.error import TelegramError

# ─── Configuration ───────────────────────────────────────────────────────────

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8645966729:AAGTs8HfpLrLg5Asn4BsdEnE9FlumiSUISc")
CHANNEL_USERNAME = "@Free_Ethio_server_FES"

# SlipNet server definitions (hardcoded from the encrypted configs you provided)
SERVERS = {
    "uk": {
        "name": "UK-Free_Ethio_server",
        "label": "🇬🇧 United Kingdom",
        "dnstt_nameserver": "gbrd.hackkcah.xyz",
        "dnstt_public_key": "a4cc7c552d8b70553b5676be703858aad620008f47b98a1e8c925f2273dc2875",
        "tunnel_type": "17",  # DNSTT+SSH
    },
    "germany": {
        "name": "DE-Free_Ethio_server",
        "label": "🇩🇪 Germany",
        "dnstt_nameserver": "deud.hackkcah.xyz",
        "dnstt_public_key": "a4cc7c552d8b70553b5676be703858aad620008f47b98a1e8c925f2273dc2875",
        "tunnel_type": "17",  # DNSTT+SSH
    },
}

# DNS resolvers: IP:port:priority (comma-separated)
RESOLVERS = "1.1.1.1:53:1,8.8.8.8:53:2"

# Conversation states
SELECTING_SERVER, ENTERING_SSH_USERNAME, ENTERING_SSH_PASSWORD = range(3)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ─── Helper Functions ────────────────────────────────────────────────────────

async def is_user_in_channel(bot, user_id: int) -> bool:
    """Check if a user is a member of the required Telegram channel."""
    try:
        chat_member = await bot.get_chat_member(
            chat_id=CHANNEL_USERNAME, user_id=user_id
        )
        return chat_member.status in (
            chat_member.MEMBER,
            chat_member.OWNER,
            chat_member.ADMINISTRATOR,
        )
    except TelegramError as e:
        logger.warning(f"Channel membership check failed for user {user_id}: {e}")
        return False


def build_slipnet_uri(
    server_key: str,
    ssh_user: str,
    ssh_pass: str,
) -> str:
    """
    Build a slipnet:// URI from server definition + SSH credentials.

    The URI format is: slipnet://<base64url(pipe-delimited-fields)>

    Field layout (0-indexed, pipe-delimited):
        0:  tunnel_type       - "17" (DNSTT+SSH)
        1:  profile_name      - e.g. "UK-Free_Ethio_server"
        2:  source_channel    - "@Free_Ethio_server_FES"
        3:  dnstt_nameserver  - e.g. "gbrd.hackkcah.xyz"
        4:  resolvers         - "IP:port:priority,IP:port:priority"
        5:  flag              - "1"
        6:  mtu               - "5000"
        7:  congestion_ctrl   - "bbr"
        8:  proxy_port        - "1080"
        9:  listen_addr       - "127.0.0.1"
        10: flag              - "0"
        11: dnstt_public_key  - 64-char hex
        12: ssh_username      - user provided
        13: ssh_password      - user provided
        14: ssh_auth_method   - "0" (password)
        15: ssh_username      - duplicate
        16: ssh_password      - duplicate
        17: ssh_port          - "22"
        18: flag              - "0"
        19: listen_addr       - "127.0.0.1"
        20: flag              - "0"
        21: empty
        22: dns_transport     - "udp"
        23: proxy_password    - empty
        24: empty
        25: empty
        26: empty
        27: naive_port        - "443"
        28: empty
        29: empty
        30: empty
        31: empty
        32: flag              - "0"
        33: flag              - "0"
        34: flag              - "0"
        35: flag              - "0"
    """
    srv = SERVERS[server_key]

    fields = [
        srv["tunnel_type"],                                  # 0
        srv["name"],                                         # 1
        CHANNEL_USERNAME,                                    # 2
        srv["dnstt_nameserver"],                             # 3
        RESOLVERS,                                           # 4
        "1",                                                 # 5
        "5000",                                              # 6
        "bbr",                                               # 7
        "1080",                                              # 8
        "127.0.0.1",                                         # 9
        "0",                                                 # 10
        srv["dnstt_public_key"],                             # 11
        ssh_user,                                            # 12
        ssh_pass,                                            # 13
        "0",                                                 # 14
        ssh_user,                                            # 15
        ssh_pass,                                            # 16
        "22",                                                # 17
        "0",                                                 # 18
        "127.0.0.1",                                         # 19
        "0",                                                 # 20
        "",                                                  # 21
        "udp",                                               # 22
        "",                                                  # 23
        "",                                                  # 24
        "",                                                  # 25
        "",                                                  # 26
        "443",                                               # 27
        "",                                                  # 28
        "",                                                  # 29
        "",                                                  # 30
        "",                                                  # 31
        "0",                                                 # 32
        "0",                                                 # 33
        "0",                                                 # 34
        "0",                                                 # 35
    ]

    # Build pipe-delimited string
    raw = "|".join(fields)

    # Base64url encode (RFC 4648, no padding)
    encoded = base64.urlsafe_b64encode(raw.encode()).rstrip(b"=").decode()

    return f"slipnet://{encoded}"


# ─── Command Handlers ────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command."""
    user = update.effective_user

    # Check channel membership
    if not await is_user_in_channel(context.bot, user.id):
        keyboard = [
            [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/Free_Ethio_server_FES")],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"👋 Welcome {user.first_name}!\n\n"
            f"You must join our channel to use this bot:\n"
            f"👉 {CHANNEL_USERNAME}\n\n"
            f"After joining, click the button below to continue.",
            reply_markup=reply_markup,
        )
        return ConversationHandler.END

    return await show_server_selection(update, context)


async def show_server_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Show server selection inline keyboard."""
    keyboard = [
        [InlineKeyboardButton(SERVERS["uk"]["label"], callback_data="server_uk")],
        [InlineKeyboardButton(SERVERS["germany"]["label"], callback_data="server_germany")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "🌍 *Select a Server*\n\n"
        "Choose the server location for your SlipNet VPN config:\n\n"
        f"🇬🇧 *UK Server* — `{SERVERS['uk']['dnstt_nameserver']}`\n"
        f"🇩🇪 *Germany Server* — `{SERVERS['germany']['dnstt_nameserver']}`\n\n"
        "You'll need SSH credentials from hackkcah.com."
    )

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup,
                                         parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )

    return SELECTING_SERVER


async def handle_server_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle server selection from inline keyboard."""
    query = update.callback_query
    await query.answer()

    # Store selected server
    data = query.data  # "server_uk" or "server_germany"
    server_key = data.replace("server_", "")
    context.user_data["server_key"] = server_key

    server_label = SERVERS[server_key]["label"]

    # Check membership again (user may have clicked "I've Joined")
    if data == "check_membership":
        if await is_user_in_channel(context.bot, query.from_user.id):
            return await show_server_selection(update, context)
        else:
            await query.edit_message_text(
                "❌ You haven't joined the channel yet.\n\n"
                f"Please join {CHANNEL_USERNAME} first, then click '✅ I've Joined'.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 Join Channel",
                                          url="https://t.me/Free_Ethio_server_FES")],
                    [InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")],
                ]),
            )
            return ConversationHandler.END

    # Verify membership for server selection
    if not await is_user_in_channel(context.bot, query.from_user.id):
        await query.edit_message_text(
            "❌ Access Denied\n\n"
            f"You must join {CHANNEL_USERNAME} to use this bot.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Join Channel",
                                      url="https://t.me/Free_Ethio_server_FES")],
            ]),
        )
        return ConversationHandler.END

    # Ask for SSH username
    await query.edit_message_text(
        f"{server_label} selected!\n\n"
        "📝 *Step 1: Enter your SSH Username*\n\n"
        "Go to https://hackkcah.com and create a free SSH account "
        f"for the **{server_label}** server.\n\n"
        f"Type your SSH username below:",
        parse_mode="Markdown",
    )
    return ENTERING_SSH_USERNAME


async def handle_ssh_username(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Receive SSH username from user."""
    ssh_user = update.message.text.strip()

    if not ssh_user or len(ssh_user) > 64:
        await update.message.reply_text(
            "❌ Invalid username. Please enter a valid SSH username (max 64 characters)."
        )
        return ENTERING_SSH_USERNAME

    context.user_data["ssh_user"] = ssh_user

    # Ask for SSH password
    await update.message.reply_text(
        f"✅ SSH Username: `{ssh_user}`\n\n"
        "📝 *Step 2: Enter your SSH Password*\n\n"
        "Now enter the SSH password for your hackkcah.com account:\n\n"
        "⚠️ Your password is only used to generate the config and is not stored.",
        parse_mode="Markdown",
    )
    return ENTERING_SSH_PASSWORD


async def handle_ssh_password(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Receive SSH password and generate config."""
    ssh_pass = update.message.text.strip()
    ssh_user = context.user_data.get("ssh_user", "")
    server_key = context.user_data.get("server_key", "uk")

    if not ssh_pass or len(ssh_pass) > 64:
        await update.message.reply_text(
            "❌ Invalid password. Please enter a valid SSH password (max 64 characters)."
        )
        return ENTERING_SSH_PASSWORD

    # Verify channel membership one more time
    if not await is_user_in_channel(context.bot, update.effective_user.id):
        await update.message.reply_text(
            "❌ You have left the channel. Please re-join and try again.\n"
            f"{CHANNEL_USERNAME}"
        )
        return ConversationHandler.END

    # Generate the slipnet:// URI
    try:
        slipnet_uri = build_slipnet_uri(server_key, ssh_user, ssh_pass)
    except Exception as e:
        logger.error(f"Failed to generate URI: {e}")
        await update.message.reply_text(
            "❌ An error occurred while generating your config. Please try again with /start."
        )
        return ConversationHandler.END

    srv = SERVERS[server_key]
    server_label = srv["label"]

    # Build response
    response = (
        f"✅ *Your SlipNet Config is Ready!*\n\n"
        f"🌍 *Server:* {server_label}\n"
        f"👤 *SSH User:* `{ssh_user}`\n"
        f"🔗 *Nameserver:* `{srv['dnstt_nameserver']}`\n\n"
        f"📋 *Copy the link below and import it in SlipNet:*\n\n"
        f"`{slipnet_uri}`\n\n"
        "📱 *How to use:*\n"
        "1. Open SlipNet app on Android\n"
        "2. Tap the + button → Import Profile\n"
        "3. Paste the URI above\n"
        "4. Connect and enjoy!\n\n"
        "💡 *Need SSH credentials?*\n"
        f"Create a free account at:\n"
        f"https://hackkcah.com\n\n"
        "⚡ Config is valid as long as your hackkcah SSH account is active."
    )

    await update.message.reply_text(response, parse_mode="Markdown")

    # Clean up user data
    context.user_data.clear()

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text(
        "❌ Operation cancelled. Send /start to begin again."
    )
    context.user_data.clear()
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    text = (
        "🆘 *Free Ethio Server Bot Help*\n\n"
        "This bot generates SlipNet VPN configs using SSH credentials from hackkcah.com.\n\n"
        "*Commands:*\n"
        "• `/start` — Begin the config generation process\n"
        "• `/help` — Show this help message\n"
        "• `/cancel` — Cancel the current operation\n\n"
        "*How it works:*\n"
        "1. Join the channel: @Free_Ethio_server_FES\n"
        "2. Send /start\n"
        "3. Select a server (UK or Germany)\n"
        "4. Enter your hackkcah.com SSH username & password\n"
        "5. Copy the generated slipnet:// URI into SlipNet\n\n"
        "*Need an SSH account?*\n"
        "Go to https://hackkcah.com and create a free SSH account "
        "for the server you selected.\n"
        "Use the Germany (DE Free) or UK (GB Free) server options.\n\n"
        "Made with ❤️ for the Free Ethio Server community."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle orphan callbacks (fallback)."""
    query = update.callback_query
    await query.answer()

    if query.data == "check_membership":
        if await is_user_in_channel(context.bot, query.from_user.id):
            await query.edit_message_text("✅ Membership confirmed! Use /start to begin.")
        else:
            await query.edit_message_text(
                "❌ You haven't joined yet.\n"
                f"Please join {CHANNEL_USERNAME} first.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 Join Channel",
                                          url="https://t.me/Free_Ethio_server_FES")],
                ]),
            )


# ─── Main Application ─────────────────────────────────────────────────────────

def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("ERROR: BOT_TOKEN not set. Set the BOT_TOKEN environment variable.")
        sys.exit(1)

    # Build application
    application = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler for the main flow
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_SERVER: [
                CallbackQueryHandler(
                    handle_server_selection,
                    pattern=r"^(server_uk|server_germany|check_membership)$",
                ),
            ],
            ENTERING_SSH_USERNAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, handle_ssh_username
                ),
            ],
            ENTERING_SSH_PASSWORD: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, handle_ssh_password
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),  # restart at any point
        ],
        name="slipnet_generator",
        persistent=False,
    )

    # Register handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        CallbackQueryHandler(callback_handler, pattern="^check_membership$")
    )

    # Start polling
    logger.info("Starting Free Ethio SlipNet Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
