import base64
import logging
import socket
from flask import Flask, request
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
BOT_TOKEN = "8645966729:AAHuD7KiVQU0BCzLBIljiBOKohH2n43gydY"
REQUIRED_CHANNEL = "@Free_Ethio_server_FES"
CHANNEL_INVITE = "https://t.me/Free_Ethio_server_FES"

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# SERVER CONFIG (hackkcah.com infrastructure)
# ──────────────────────────────────────────────
SERVERS = {
    "germany": {
        "name": "Germany",
        "ssh_host": "deu.hackkcah.xyz",
        "dnstt_domain": "deud.hackkcah.xyz",
        "public_key": "a4cc7c552d8b70553b5676be703858aad620008f47b98a1e8c925f2273dc2875",
        "flag": "🇩🇪",
    },
    "uk": {
        "name": "UK",
        "ssh_host": "gbr.hackkcah.xyz",
        "dnstt_domain": "gbrd.hackkcah.xyz",
        "public_key": "a4cc7c552d8b70553b5676be703858aad620008f47b98a1e8c925f2273dc2875",
        "flag": "🇬🇧",
    },
}


def resolve_ip(hostname: str) -> str:
    """Resolve hostname to IP address (slipgate's getServerIP() equivalent)."""
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return hostname


# ──────────────────────────────────────────────
# SLIPNET URI GENERATOR (60 fields, config v22)
# Based on slipgate v1.6.4 internal/clientcfg/
# ──────────────────────────────────────────────
def generate_slipnet_uri(
    server_key: str, ssh_user: str, ssh_pass: str, profile_name: str = None
) -> str:
    """
    Generate a 60-field slipnet:// URI for SlipNet v2.5.3+ (config v22).
    Tunnel type: dnstt_ssh (maps to SlipNet tunnel type 17).
    """
    server = SERVERS[server_key]
    ssh_ip = resolve_ip(server["ssh_host"])

    if profile_name is None:
        profile_name = f"{server['name']}"

    fields = [""] * 60

    # 0: config version
    fields[0] = "22"
    # 1: tunnel type
    fields[1] = "dnstt_ssh"
    # 2: profile name
    fields[2] = profile_name
    # 3: DNSTT nameserver domain
    fields[3] = server["dnstt_domain"]
    # 4: resolvers
    fields[4] = "8.8.8.8:53:0"
    # 5: auth mode
    fields[5] = "0"
    # 6: keepalive (ms)
    fields[6] = "5000"
    # 7: congestion control
    fields[7] = "bbr"
    # 8: TCP listen port
    fields[8] = "1080"
    # 9: TCP listen host
    fields[9] = "127.0.0.1"
    # 10: GSO enabled
    fields[10] = "0"
    # 11: public key (hex)
    fields[11] = server["public_key"]
    # 12: SOCKS user
    fields[12] = ""
    # 13: SOCKS pass
    fields[13] = ""
    # 14: SSH enabled (1 = SSH backend)
    fields[14] = "1"
    # 15: SSH username
    fields[15] = ssh_user
    # 16: SSH password
    fields[16] = ssh_pass
    # 17: SSH port
    fields[17] = "22"
    # 18: Forward DNS through SSH (deprecated)
    fields[18] = "0"
    # 19: SSH host (server IP)
    fields[19] = ssh_ip
    # 20: Use server DNS (deprecated)
    fields[20] = "0"
    # 21: DoH URL
    fields[21] = ""
    # 22: DNS transport
    fields[22] = "udp"
    # 23: SSH auth type
    fields[23] = "password"
    # 24: SSH private key (base64)
    fields[24] = ""
    # 25: SSH key passphrase (base64)
    fields[25] = ""
    # 26: Tor bridge lines (base64)
    fields[26] = ""
    # 27: DNSTT authoritative
    fields[27] = "0"
    # 28: NaiveProxy port
    fields[28] = "0"
    # 29: NaiveProxy user
    fields[29] = ""
    # 30: NaiveProxy pass
    fields[30] = ""
    # 31: Is locked
    fields[31] = "0"
    # 32: Lock password hash
    fields[32] = ""
    # 33: Expiration date
    fields[33] = "0"
    # 34: Allow sharing
    fields[34] = "0"
    # 35: Bound device ID
    fields[35] = ""
    # 36: Resolvers hidden
    fields[36] = "0"
    # 37: Hidden resolvers
    fields[37] = ""
    # 38: NoizDNS stealth
    fields[38] = "0"
    # 39: DNS payload size
    fields[39] = "0"
    # 40: SOCKS5 server port
    fields[40] = "1080"
    # 41-49: VayDNS fields (all disabled)
    fields[41] = "0"
    fields[42] = "0"
    fields[43] = "0"
    fields[44] = "0"
    fields[45] = "0"
    fields[46] = "0"
    fields[47] = "0"
    fields[48] = "0"
    fields[49] = "0"
    # 50: SSH over TLS enabled
    fields[50] = "0"
    # 51: SSH TLS SNI
    fields[51] = ""
    # 52: SSH TLS proxy host
    fields[52] = ""
    # 53: SSH TLS proxy port
    fields[53] = ""
    # 54: SSH TLS insecure
    fields[54] = ""
    # 55: SSH over WebSocket enabled
    fields[55] = "0"
    # 56: SSH WS path
    fields[56] = "/"
    # 57: SSH WS use TLS
    fields[57] = "1"
    # 58: SSH WS custom host
    fields[58] = ""
    # 59: SSH payload (base64)
    fields[59] = ""

    # Encode: pipe-join + standard base64 (with padding)
    pipe_data = "|".join(fields)
    encoded = base64.b64encode(pipe_data.encode()).decode()
    return f"slipnet://{encoded}"


# ──────────────────────────────────────────────
# TELEGRAM BOT HANDLERS
# ──────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Welcome {user.first_name}!\n\n"
        f"This bot generates SlipNet VPN configurations for Germany 🇩🇪 and UK 🇬🇧 servers.\n\n"
        f"⚠️ *Before using this bot, you MUST join:*\n"
        f"{CHANNEL_INVITE}\n\n"
        f"📌 *Requirements:*\n"
        f"• Create an account at https://hackkcah.com to get SSH credentials\n"
        f"• Join {REQUIRED_CHANNEL}\n"
        f"• Have SlipNet v2.5.3+ installed\n\n"
        f"Type /config to generate your config, or /help for more info.",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    await update.message.reply_text(
        "🔹 *Available Commands:*\n"
        "/start - Welcome message\n"
        "/help - Show this help\n"
        "/config - Generate a SlipNet config\n"
        "/servers - Show available servers\n\n"
        "🔹 *How to use:*\n"
        "1. Join @Free_Ethio_server_FES\n"
        "2. Create SSH account at https://hackkcah.com\n"
        "3. Run /config and choose your server\n"
        "4. Enter your SSH username and password\n"
        "5. Import the generated URI into SlipNet\n\n"
        "🔹 *Need help?* Contact @Free_Ethio_server_FES",
        parse_mode="Markdown",
    )


async def servers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available servers."""
    keyboard = [
        [InlineKeyboardButton(f"{SERVERS['germany']['flag']} Germany", callback_data="info_germany")],
        [InlineKeyboardButton(f"{SERVERS['uk']['flag']} UK", callback_data="info_uk")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌍 *Available Servers:*\n\n"
        f"{SERVERS['germany']['flag']} *Germany* - {SERVERS['germany']['ssh_host']}\n"
        f"{SERVERS['uk']['flag']} *UK* - {SERVERS['uk']['ssh_host']}\n\n"
        "Both use DNSTT tunneling with SSH backend.\n\n"
        "Select a server for details:",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start config generation - ask for server selection."""
    # Check channel membership
    try:
        chat_member = await context.bot.get_chat_member(
            chat_id=REQUIRED_CHANNEL, user_id=update.effective_user.id
        )
        if chat_member.status in ("left", "kicked", "banned"):
            await update.message.reply_text(
                f"❌ You must join {REQUIRED_CHANNEL} first!\n\n"
                f"Join here: {CHANNEL_INVITE}\n\n"
                f"After joining, run /config again.",
            )
            return
    except Exception:
        # If we can't check, proceed anyway
        pass

    keyboard = [
        [InlineKeyboardButton(f"{SERVERS['germany']['flag']} Germany 🇩🇪", callback_data="server_germany")],
        [InlineKeyboardButton(f"{SERVERS['uk']['flag']} UK 🇬🇧", callback_data="server_uk")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌍 *Select your server:*",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("info_"):
        server_key = data.replace("info_", "")
        srv = SERVERS[server_key]
        await query.edit_message_text(
            f"{srv['flag']} *{srv['name']}*\n\n"
            f"SSH Host: `{srv['ssh_host']}`\n"
            f"DNSTT Domain: `{srv['dnstt_domain']}`\n"
            f"Public Key: `{srv['public_key'][:20]}...`\n"
            f"Tunnel Type: `dnstt_ssh`\n\n"
            f"Run /config to generate a config for this server.",
            parse_mode="Markdown",
        )

    elif data.startswith("server_"):
        # User selected a server - store it and ask for SSH credentials
        server_key = data.replace("server_", "")
        context.user_data["selected_server"] = server_key
        srv = SERVERS[server_key]

        await query.edit_message_text(
            f"You selected: {srv['flag']} {srv['name']}\n\n"
            f"Now, please enter your SSH *username* from https://hackkcah.com:",
            parse_mode="Markdown",
        )
        context.user_data["awaiting"] = "ssh_username"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (SSH credentials input)."""
    awaiting = context.user_data.get("awaiting")
    if not awaiting:
        await update.message.reply_text(
            "Use /config to start generating a config, or /help for available commands."
        )
        return

    text = update.message.text.strip()

    if awaiting == "ssh_username":
        context.user_data["ssh_user"] = text
        context.user_data["awaiting"] = "ssh_password"
        await update.message.reply_text(
            "✅ SSH username saved!\n\nNow enter your SSH *password* from https://hackkcah.com:",
            parse_mode="Markdown",
        )

    elif awaiting == "ssh_password":
        ssh_user = context.user_data.get("ssh_user", "")
        ssh_pass = text
        server_key = context.user_data.get("selected_server", "germany")
        srv = SERVERS[server_key]

        # Generate the URI
        try:
            uri = generate_slipnet_uri(server_key, ssh_user, ssh_pass)

            await update.message.reply_text(
                f"✅ *Config Generated!*\n\n"
                f"🌍 Server: {srv['flag']} {srv['name']}\n"
                f"👤 SSH: `{ssh_user}`\n"
                f"🔑 Public Key: `{srv['public_key'][:20]}...`\n\n"
                f"📋 *Your SlipNet URI:*\n"
                f"```\n{uri}\n```\n\n"
                f"📱 *How to import:*\n"
                f"1. Copy the full URI above\n"
                f"2. Open SlipNet app\n"
                f"3. Tap + or Import\n"
                f"4. Paste the URI\n\n"
                f"⚠️ *Keep your credentials private!*",
                parse_mode="Markdown",
            )

            # Also send as a separate message with just the URI for easy copying
            await update.message.reply_text(uri)

        except Exception as e:
            logger.error(f"Config generation error: {e}")
            await update.message.reply_text(
                f"❌ Error generating config: {str(e)}\n\nPlease try again with /config",
            )

        # Reset state
        context.user_data.clear()


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.warning(f"Update {update} caused error {context.error}")


# ──────────────────────────────────────────────
# FLASK WEBHOOK SETUP (for Railway)
# ──────────────────────────────────────────────
app = Flask(__name__)


@app.route("/")
def index():
    return "SlipNet VPN Bot is running!", 200


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """Handle incoming Telegram updates via webhook."""
    update = Update.de_json(request.get_json(force=True), bot)
    application.process_update(update)
    return "OK", 200


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
if __name__ == "__main__":
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("servers", servers_command))
    application.add_handler(CommandHandler("config", config_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    # Initialize bot for Flask webhook
    bot = application.bot

    # Set webhook
    import os
    railway_url = os.environ.get("RAILWAY_URL", "https://slipnet-bot.up.railway.app")
    webhook_url = f"{railway_url}/{BOT_TOKEN}"

    # Run Flask (Railway will use the PORT env variable)
    port = int(os.environ.get("PORT", 8080))

    # Set webhook on startup
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        bot.set_webhook(url=webhook_url, allowed_updates=Update.ALL_TYPES)
    )
    logger.info(f"Webhook set to: {webhook_url}")

    # Start Flask
    app.run(host="0.0.0.0", port=port)
