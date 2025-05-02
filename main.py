import os
import logging
import json
import datetime

from matplotlib.backend_bases import button_press_handler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler
import aiohttp
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import matplotlib

matplotlib.use('Agg')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation handler
MAIN_MENU, TOKEN_SELECTION, ACCOUNT_SELECTION, INFO_SELECTION = range(4)

# Configuration
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8125089797:AAHCrOT5c45gLgo1uscgXXOgWeDQJ_dNz88")
VYBE_API_KEY = os.environ.get("VYBE_API_KEY", "ZYofNVCsyqxkcTDNNvo9MhCSyFBmNe35QMLTcts9BtThuCFE")
VYBE_API_BASE_URL = "https://api.vybenetwork.xyz"

# Top Solana tokens (examples - you may want to get these from the tokens endpoint)
TOP_TOKENS = [
    "SOL", "BONK", "JTO", "PYTH", "RAY",
    "ORCA", "MSOL", "RENDER", "JITO", "DFL"
]

# Available info types
AVAILABLE_INFO = {
    "token_details": "Token Details",
    "token_holders": "Top Holders",
    "token_volume": "Transfer Volume",
    "token_holders_ts": "Holders Trend"
}


# Helper Functions
async def fetch_from_vybe_api(endpoint, params=None):
    """Fetch data from Vybe API."""
    headers = {
        "accept": "application/json",
        "X-API-KEY": VYBE_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        url = f"{VYBE_API_BASE_URL}/{endpoint}"
        logger.info(f"Making API request to: {url}")
        logger.info(f"With params: {params}")

        try:
            async with session.get(url, headers=headers, params=params) as response:
                response_text = await response.text()
                logger.info(f"Response status: {response.status}")
                logger.info(f"Response body: {response_text[:200] if len(response_text) > 200 else response_text}...")

                if response.status == 200:
                    try:
                        # Try to parse JSON
                        return await response.json()
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON: {response_text}")
                        return {"error": "Invalid JSON response"}
                else:
                    logger.error(f"API Error: {response.status} - {response_text}")
                    return {"error": f"API returned status code {response.status}"}
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return {"error": str(e)}


async def post_to_vybe_api(endpoint, data):
    """Post data to Vybe API."""
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-KEY": VYBE_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        url = f"{VYBE_API_BASE_URL}/{endpoint}"
        logger.info(f"Making API POST request to: {url}")

        try:
            async with session.post(url, headers=headers, json=data) as response:
                response_text = await response.text()
                logger.info(f"Response status: {response.status}")
                logger.info(f"Response body: {response_text[:200] if len(response_text) > 200 else response_text}...")

                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API Error: {response.status} - {response_text}")
                    return {"error": f"API returned status code {response.status}"}
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return {"error": str(e)}


async def get_token_mint_address(symbol):
    """Get token mint address from symbol."""
    # We'd need to fetch this from the tokens endpoint
    # For now, this is a placeholder
    tokens = await fetch_from_vybe_api("tokens")
    if "error" in tokens:
        return None

    for token in tokens.get("tokens", []):
        if token.get("symbol") == symbol:
            return token.get("mintAddress")

    return None

async def generate_token_chart(data, chart_type, token_name):
    """Generate a chart based on the token data and chart type."""
    if not data:
        return None

    try:
        # Convert data to pandas DataFrame
        df = pd.DataFrame(data)

        # Create figure
        plt.figure(figsize=(10, 6))

        if chart_type == "price":
            plt.plot(df['date'], df['price'], color='blue')
            plt.title(f"{token_name} Price Chart")
            plt.ylabel("Price (USD)")
        elif chart_type == "holders":
            plt.plot(df['date'], df['holders'], color='green')
            plt.title(f"{token_name} Holders Count")
            plt.ylabel("Number of Holders")
        elif chart_type == "volume":
            plt.bar(df['date'], df['volume'], color='purple', alpha=0.7)
            plt.title(f"{token_name} Transfer Volume")
            plt.ylabel("Volume (USD)")

        plt.xlabel("Date")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # Save to BytesIO object
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close()

        return buffer
    except Exception as e:
        logger.error(f"Error generating chart: {str(e)}")
        return None


# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""
    user = update.effective_user

    welcome_message = (
        f"Hello {user.first_name}! 👋\n\n"
        f"Welcome to *VybeNetworkBot* - your Solana blockchain data assistant. "
        f"I provide insights from Vybe.fyi API to help you track tokens, wallets, and market activity.\n\n"
        f"What would you like to explore today?"
    )

    keyboard = [
        [InlineKeyboardButton("🪙 Token Information", callback_data="token_info")],
        [InlineKeyboardButton("👛 Wallet Analysis", callback_data="wallet_analysis")],
        [InlineKeyboardButton("🌐 Network Stats", callback_data="network_stats")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    return MAIN_MENU


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "*VybeNetworkBot Commands:*\n\n"
        "/start - Start the bot and show main menu\n"
        "/help - Show this help message\n"
        "/tokens - Get token information\n"
        "/wallet <address> - Get wallet analysis\n"
        "/status - Check bot and API status\n\n"

        "*Available Information:*\n"
        "• Token Details - Basic token information and metrics\n"
        "• Top Holders - List of top wallet addresses holding a token\n"
        "• Transfer Volume - Historical volume of token transfers\n"
        "• Holders Trend - Growth of token holders over time\n\n"

        "This bot is powered by the Vybe.fyi API, a comprehensive Solana data platform."
    )

    await update.message.reply_text(help_text, parse_mode='Markdown', disable_web_page_preview=True)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check bot and API status."""
    # Test Vybe API connection with a known working endpoint
    try:
        api_response = await fetch_from_vybe_api("account/known-accounts")
        api_status = "✅ Online" if not api_response.get("error") else f"❌ Error: {api_response.get('error')}"
    except Exception as e:
        api_status = f"❌ Error: {str(e)}"

    status_text = (
        "*VybeNetworkBot Status*\n\n"
        f"Bot Status: ✅ Online\n"
        f"Vybe API: {api_status}\n"
        f"Last Update: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"This bot provides Solana blockchain data using the Vybe.fyi API."
    )

    await update.message.reply_text(status_text, parse_mode='Markdown')


async def tokens_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Triggered by /tokens command - show token selection."""
    return await show_token_selection(update, context)


async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Triggered by /wallet <address> command."""
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "Please specify a wallet address. Example: `/wallet 3XAU...j7Ux`",
            parse_mode='Markdown'
        )
        return

    address = context.args[0]

    # Show loading message
    message = await update.message.reply_text("Fetching wallet data...")

    try:
        # Fetch token balance data
        balance_data = await fetch_from_vybe_api(f"account/token-balance/{address}")

        if "error" in balance_data:
            await message.edit_text(f"Error fetching wallet data: {balance_data['error']}")
            return

        # Process data
        total_value_usd = balance_data.get("totalValueUsd", 0)
        total_value_sol = balance_data.get("totalValueSol", 0)
        tokens = balance_data.get("tokens", [])

        # Analysis text
        analysis_text = (
            f"*Wallet Analysis: {address[:6]}...{address[-4:]}*\n\n"
            f"💰 *Total Value:* ${total_value_usd:,.2f} (≈{total_value_sol:,.2f} SOL)\n"
            f"🪙 *Token Count:* {len(tokens)}\n\n"
            f"*Top Tokens by Value:*\n"
        )

        # Sort tokens by USD value and take top 5
        tokens.sort(key=lambda x: x.get("valueUsd", 0), reverse=True)
        for i, token in enumerate(tokens[:5], 1):
            symbol = token.get("symbol", "Unknown")
            balance = token.get("balance", 0)
            value = token.get("valueUsd", 0)
            analysis_text += f"{i}. {symbol}: {balance:,.4f} (${value:,.2f})\n"

        # Create keyboard with analysis options
        keyboard = [
            [InlineKeyboardButton("View NFT Balances", callback_data=f"nft_balance:{address}")],
            [InlineKeyboardButton("View PnL", callback_data=f"pnl:{address}")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Update the loading message with the analysis
        await message.edit_text(
            analysis_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        await message.edit_text(f"Error processing wallet data: {str(e)}")


# Callback Query Handlers
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button press."""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "token_info":
        return await show_token_selection(update, context)
    elif data == "wallet_analysis":
        await show_wallet_input(update, context)
        return MAIN_MENU
    elif data == "network_stats":
        await show_network_stats(update, context)
        return MAIN_MENU
    elif data == "help":
        await show_help(update, context)
        return MAIN_MENU
    elif data == "back_to_main":
        return await show_main_menu(update, context)
    elif data.startswith("token:"):
        _, token = data.split(":")
        context.user_data["selected_token"] = token
        return await show_info_selection(update, context)
    elif data.startswith("info:"):
        _, info_type = data.split(":")
        context.user_data["selected_info"] = info_type
        await show_token_info(update, context)
        return MAIN_MENU
    elif data.startswith("nft_balance:") or data.startswith("pnl:"):
        parts = data.split(":")
        action_type = parts[0]
        address = parts[1]
        await show_wallet_detail(update, context, action_type, address)
        return MAIN_MENU

    return MAIN_MENU


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the main menu."""
    keyboard = [
        [InlineKeyboardButton("🪙 Token Information", callback_data="token_info")],
        [InlineKeyboardButton("👛 Wallet Analysis", callback_data="wallet_analysis")],
        [InlineKeyboardButton("🌐 Network Stats", callback_data="network_stats")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "What would you like to explore today?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "What would you like to explore today?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    return MAIN_MENU


async def show_network_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show Solana network statistics."""
    query = update.callback_query

    # Show loading message
    await query.edit_message_text("Fetching network statistics...")

    try:
        # Fetch program ranking data
        program_data = await fetch_from_vybe_api("program/ranking")

        if "error" in program_data:
            await query.edit_message_text(f"Error fetching program data: {program_data['error']}")
            return

        # Process data for a network overview
        programs = program_data.get("programs", [])
        top_programs = sorted(programs, key=lambda x: x.get("dailyActiveUsers", 0), reverse=True)[:5]

        stats_text = (
            f"*Solana Network Statistics*\n\n"
            f"🧩 *Total Tracked Programs:* {len(programs)}\n\n"
            f"*Top Programs by Daily Active Users:*\n"
        )

        for i, program in enumerate(top_programs, 1):
            name = program.get("name", "Unknown Program")
            address = program.get("programId", "")
            users = program.get("dailyActiveUsers", 0)
            stats_text += f"{i}. {name}: {users:,} users\n"

        keyboard = [
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        await query.edit_message_text(f"Error processing network data: {str(e)}")


async def show_token_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show token selection buttons."""
    # Fetch tokens from the API
    try:
        tokens_data = await fetch_from_vybe_api("tokens")

        if "error" in tokens_data:
            if update.callback_query:
                await update.callback_query.edit_message_text(f"Error fetching tokens: {tokens_data['error']}")
            else:
                await update.message.reply_text(f"Error fetching tokens: {tokens_data['error']}")
            return MAIN_MENU

        # Get top tokens by market cap
        all_tokens = tokens_data.get("tokens", [])
        top_tokens = sorted(all_tokens, key=lambda x: x.get("marketCap", 0), reverse=True)[:15]

        message = "Select a token to analyze:"

        # Create a keyboard with 3 tokens per row
        keyboard = []
        row = []
        for i, token in enumerate(top_tokens):
            symbol = token.get("symbol", "Unknown")
            row.append(InlineKeyboardButton(symbol, callback_data=f"token:{symbol}"))
            if (i + 1) % 3 == 0 or i == len(top_tokens) - 1:
                keyboard.append(row)
                row = []

        keyboard.append([InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=reply_markup
            )

    except Exception as e:
        msg = f"Error loading token selection: {str(e)}"
        if update.callback_query:
            await update.callback_query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)

    return TOKEN_SELECTION


async def show_wallet_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show wallet address input instructions."""
    query = update.callback_query

    wallet_text = (
        "*👛 Wallet Analysis*\n\n"
        "To analyze a Solana wallet, use the following command:\n"
        "`/wallet <address>`\n\n"
        "Example: `/wallet 3XAuTiVHG7JzRRFY9GGMc6x8SziC6X3hQS2AJVWi7j7x`\n\n"
        "This will show you token balances, NFT holdings, and transaction history."
    )

    keyboard = [[InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        wallet_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def show_info_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show information type selection buttons."""
    token = context.user_data.get("selected_token", "")
    message = f"What information would you like to see about {token}?"

    keyboard = []
    for info_id, info_name in AVAILABLE_INFO.items():
        keyboard.append([InlineKeyboardButton(info_name, callback_data=f"info:{info_id}")])

    keyboard.append([InlineKeyboardButton("Back", callback_data="token_info")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup
    )

    return INFO_SELECTION


async def show_token_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show token information based on selected options."""
    query = update.callback_query

    token = context.user_data.get("selected_token", "")
    info_type = context.user_data.get("selected_info", "")

    # Show loading message
    await query.edit_message_text(f"Fetching {AVAILABLE_INFO[info_type]} for {token}...")

    try:
        # Get token mint address
        mint_address = await get_token_mint_address(token)

        if not mint_address:
            await query.edit_message_text(f"Error: Could not find mint address for {token}")
            return

        # Fetch data based on info type
        if info_type == "token_details":
            data = await fetch_from_vybe_api(f"token/{mint_address}")
            await show_token_details(query, token, data, context)
        elif info_type == "token_holders":
            data = await fetch_from_vybe_api(f"token/{mint_address}/top-holders")
            await show_token_holders(query, token, data, context)
        elif info_type == "token_volume":
            data = await fetch_from_vybe_api(f"token/{mint_address}/transfer-volume")
            await show_token_volume(query, token, data, context)
        elif info_type == "token_holders_ts":
            data = await fetch_from_vybe_api(f"token/{mint_address}/holders-ts")
            await show_token_holders_ts(query, token, data, context)
        else:
            await query.edit_message_text(f"Unknown info type: {info_type}")

    except Exception as e:
        await query.edit_message_text(f"Error fetching token information: {str(e)}")


async def show_token_details(query, token, data, context):
    """Display token details."""
    if not isinstance(data, dict):
        logger.error(f"Expected dictionary, got {type(data)}: {data}")
        await query.edit_message_text(f"Error: Unexpected API response format")
        return

    if "error" in data:
        await query.edit_message_text(f"Error fetching token details: {data['error']}")
        return

    # Process the data
    symbol = data.get("symbol", token)
    name = data.get("name", "Unknown")
    price = data.get("price", 0)
    market_cap = data.get("marketCap", 0)
    volume_24h = data.get("volume24h", 0)
    holders = data.get("holders", 0)
    supply = data.get("currentSupply", 0)

    details_text = (
        f"*{name} ({symbol}) Details*\n\n"
        f"💰 *Price:* ${price:,.6f}\n"
        f"📊 *Market Cap:* ${market_cap:,.2f}\n"
        f"📈 *24h Volume:* ${volume_24h:,.2f}\n"
        f"👛 *Holders:* {holders:,}\n"
        f"🔢 *Supply:* {supply:,.2f}\n\n"
    )

    keyboard = [
        [InlineKeyboardButton("View Top Holders", callback_data=f"info:token_holders")],
        [InlineKeyboardButton("View Transfer Volume", callback_data=f"info:token_volume")],
        [InlineKeyboardButton("Back to Token Selection", callback_data="token_info")],
        [InlineKeyboardButton("Main Menu", callback_data="back_to_main")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        details_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def show_token_holders(query, token, data, context):
    """Display token top holders."""
    if "error" in data:
        await query.edit_message_text(f"Error fetching token holders: {data['error']}")
        return

    # Process the data
    holders = data.get("holders", [])

    if not holders:
        await query.edit_message_text(f"No holder data available for {token}")
        return

    holders_text = (
        f"*{token} Top Holders*\n\n"
        f"Total Holders: {len(holders):,}\n\n"
        f"*Top Holders by Balance:*\n"
    )

    # Take top 5 holders
    for i, holder in enumerate(holders[:5], 1):
        address = holder.get("ownerAddress", "Unknown")
        short_address = f"{address[:6]}...{address[-4:]}"
        balance = holder.get("balance", 0)
        percentage = holder.get("percentageOfSupplyHeld", 0) * 100
        holders_text += f"{i}. {short_address}: {balance:,.2f} ({percentage:.2f}%)\n"

    keyboard = [
        [InlineKeyboardButton("View Token Details", callback_data=f"info:token_details")],
        [InlineKeyboardButton("Back to Token Selection", callback_data="token_info")],
        [InlineKeyboardButton("Main Menu", callback_data="back_to_main")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        holders_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def show_token_volume(query, token, data, context):
    """Display token transfer volume over time."""
    if "error" in data:
        await query.edit_message_text(f"Error fetching token volume: {data['error']}")
        return

    # Process the data
    volumes = data.get("volumes", [])

    if not volumes:
        await query.edit_message_text(f"No volume data available for {token}")
        return

    # Calculate total and average volume
    total_volume = sum(entry.get("amount", 0) for entry in volumes)
    avg_volume = total_volume / len(volumes) if volumes else 0

    volume_text = (
        f"*{token} Transfer Volume Analysis*\n\n"
        f"Period: {volumes[0].get('date', 'Unknown')} to {volumes[-1].get('date', 'Unknown')}\n"
        f"Total Volume: ${total_volume:,.2f}\n"
        f"Average Daily Volume: ${avg_volume:,.2f}\n\n"
    )

    # Prepare data for chart
    chart_data = []
    for entry in volumes:
        chart_data.append({
            "date": entry.get("date", ""),
            "volume": entry.get("amount", 0)
        })

    # Generate and send chart
    chart_buffer = await generate_token_chart(chart_data, "volume", token)
    if chart_buffer:
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=chart_buffer,
            caption=f"{token} Transfer Volume Chart"
        )

    keyboard = [
        [InlineKeyboardButton("View Token Details", callback_data=f"info:token_details")],
        [InlineKeyboardButton("Back to Token Selection", callback_data="token_info")],
        [InlineKeyboardButton("Main Menu", callback_data="back_to_main")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        volume_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def show_token_holders_ts(query, token, data, context):
    """Display token holders trend over time."""
    if "error" in data:
        await query.edit_message_text(f"Error fetching holders trend: {data['error']}")
        return

    # Process the data
    holders_trend = data.get("holderCounts", [])

    if not holders_trend:
        await query.edit_message_text(f"No holders trend data available for {token}")
        return

    # Calculate growth metrics
    first_count = holders_trend[0].get("holders", 0) if holders_trend else 0
    last_count = holders_trend[-1].get("holders", 0) if holders_trend else 0
    growth = last_count - first_count
    growth_pct = (growth / first_count * 100) if first_count else 0

    trend_text = (
        f"*{token} Holders Growth Analysis*\n\n"
        f"Period: {holders_trend[0].get('date', 'Unknown')} to {holders_trend[-1].get('date', 'Unknown')}\n"
        f"Starting Holders: {first_count:,}\n"
        f"Current Holders: {last_count:,}\n"
        f"Growth: {growth:+,} ({growth_pct:+.2f}%)\n\n"
    )

    # Prepare data for chart
    chart_data = []
    for entry in holders_trend:
        chart_data.append({
            "date": entry.get("date", ""),
            "holders": entry.get("holders", 0)
        })

    # Generate and send chart
    chart_buffer = await generate_token_chart(chart_data, "holders", token)
    if chart_buffer:
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=chart_buffer,
            caption=f"{token} Holders Growth Chart"
        )

    keyboard = [
        [InlineKeyboardButton("View Token Details", callback_data=f"info:token_details")],
        [InlineKeyboardButton("Back to Token Selection", callback_data="token_info")],
        [InlineKeyboardButton("Main Menu", callback_data="back_to_main")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        trend_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def show_wallet_detail(update, context, action_type, address):
    """Show detailed wallet information."""
    query = update.callback_query

    # Show loading message
    await query.edit_message_text(f"Fetching wallet data for {address[:6]}...{address[-4:]}...")

    try:
        if action_type == "nft_balance":
            # Fetch NFT balance data
            nft_data = await fetch_from_vybe_api(f"account/nft-balance/{address}")

            if "error" in nft_data:
                await query.edit_message_text(f"Error fetching NFT data: {nft_data['error']}")
                return

            # Process NFT data
            nfts = nft_data.get("nfts", [])
            total_value_usd = nft_data.get("totalValueUsd", 0)
            total_value_sol = nft_data.get("totalValueSol", 0)

            nft_text = (
                f"*NFT Holdings for {address[:6]}...{address[-4:]}*\n\n"
                f"🖼️ *Total NFTs:* {len(nfts)}\n"
                f"💰 *Total Value:* ${total_value_usd:,.2f} (≈{total_value_sol:,.2f} SOL)\n\n"
                f"*Top NFTs by Value:*\n"
            )

            # Sort by value and take top 5
            nfts.sort(key=lambda x: x.get("valueUsd", 0), reverse=True)
            for i, nft in enumerate(nfts[:5], 1):
                name = nft.get("name", "Unknown NFT")
                collection = nft.get("collectionName", "Unknown Collection")
                value = nft.get("valueUsd", 0)
                nft_text += f"{i}. {name} ({collection}): ${value:,.2f}\n"

        elif action_type == "pnl":
            # Fetch PnL data
            pnl_data = await fetch_from_vybe_api(f"account/pnl/{address}")

            if "error" in pnl_data:
                await query.edit_message_text(f"Error fetching PnL data: {pnl_data['error']}")
                return

            # Process PnL data
            pnl_summary = pnl_data.get("summary", {})
            realized_pnl = pnl_summary.get("realizedPnl", 0)
            unrealized_pnl = pnl_summary.get("unrealizedPnl", 0)
            total_pnl = pnl_summary.get("totalPnl", 0)
            positions = pnl_data.get("positions", [])

            pnl_text = (
                f"*PnL Analysis for {address[:6]}...{address[-4:]}*\n\n"
                f"💵 *Realized PnL:* ${realized_pnl:,.2f}\n"
                f"📈 *Unrealized PnL:* ${unrealized_pnl:,.2f}\n"
                f"🧮 *Total PnL:* ${total_pnl:,.2f}\n\n"
                f"*Top Positions:*\n"
            )

            # Sort by PnL and take top 5
            positions.sort(key=lambda x: abs(x.get("totalPnl", 0)), reverse=True)
            for i, position in enumerate(positions[:5], 1):
                symbol = position.get("symbol", "Unknown")
                amount = position.get("amount", 0)
                pos_pnl = position.get("totalPnl", 0)
                pnl_text += f"{i}. {symbol}: {amount:,.4f} (${pos_pnl:+,.2f})\n"

        # Create keyboard for navigation
        keyboard = [
            [InlineKeyboardButton("View Token Balances", callback_data=f"wallet:{address}")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Update message with results
        if action_type == "nft_balance":
            await query.edit_message_text(
                nft_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        elif action_type == "pnl":
            await query.edit_message_text(
                pnl_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    except Exception as e:
        await query.edit_message_text(f"Error processing wallet data: {str(e)}")


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help information."""
    query = update.callback_query

    help_text = (
        "*VybeNetworkBot Help*\n\n"
        "This bot provides data from the Vybe.fyi API for Solana blockchain analysis. "
        "Here's how to use it:\n\n"

        "*Main Features:*\n"
        "• *Token Information* - Get details about Solana tokens, including price, holders, and volume\n"
        "• *Wallet Analysis* - Analyze wallet token balances, NFT holdings, and PnL\n"
        "• *Network Stats* - View statistics about Solana network activity\n\n"

        "*Available Commands:*\n"
        "/start - Start the bot and show main menu\n"
        "/help - Show this help message\n"
        "/tokens - Get token information\n"
        "/wallet <address> - Get wallet analysis\n"
        "/status - Check bot and API status\n\n"

        "This bot is powered by the Vybe.fyi API, a comprehensive Solana data platform."
    )

    keyboard = [[InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        help_text,
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )


def main():
    """Start the bot."""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("tokens", tokens_command),
        ],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(button_callback),
            ],
            TOKEN_SELECTION: [
                CallbackQueryHandler(button_callback),
            ],
            ACCOUNT_SELECTION: [
                CallbackQueryHandler(button_callback),
            ],
            INFO_SELECTION: [
                CallbackQueryHandler(button_callback),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        per_message=True
    )

    application.add_handler(conv_handler)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("wallet", wallet_command))

    application.add_handler(CallbackQueryHandler(button_callback))

    # Start the Bot
    application.run_polling()


if __name__ == "__main__":
    main()