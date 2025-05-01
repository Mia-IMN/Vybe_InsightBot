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
MAIN_MENU, ASSET_SELECTION, TIMEFRAME_SELECTION, METRIC_SELECTION = range(4)

# Configuration
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8125089797:AAHKDU3TzaeK74Vsl-KIV60UD-ddz-N-Vic")
VYBE_API_KEY = os.environ.get("VYBE_API_KEY", "ZYofNVCsyqxkcTDNNvo9MhCSyFBmNe35QMLTcts9BtThuCFE")
VYBE_API_BASE_URL = "https://api.vybenetwork.xyz"
ALPHAVYBE_BASE_URL = "https://alphavybe.fyi"

# Top crypto assets
TOP_ASSETS = [
    "BTC", "ETH", "SOL", "BNB", "XRP",
    "DOGE", "ADA", "SHIB", "DOT", "AVAX",
    "LINK", "LTC", "BCH", "UNI", "MATIC"
]

# Available metrics
AVAILABLE_METRICS = {
    "price_action": "Price Action",
    "social_sentiment": "Social Sentiment",
    "volume_analysis": "Volume Analysis",
    "funding_rates": "Funding Rates",
    "whale_activity": "Whale Activity",
    "market_dominance": "Market Dominance",
    "volatility_index": "Volatility Index"
}

# Timeframes
TIMEFRAMES = {
    "1h": "1 Hour",
    "4h": "4 Hours",
    "1d": "1 Day",
    "7d": "7 Days",
    "30d": "30 Days"
}


# Helper Functions
async def fetch_from_vybe_api(endpoint, params=None):
    """Fetch data from Vybe API."""
    headers = {
        "Authorization": f"Bearer {VYBE_API_KEY}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        url = f"{VYBE_API_BASE_URL}/{endpoint}"
        try:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API Error: {response.status} - {await response.text()}")
                    return {"error": f"API returned status code {response.status}"}
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return {"error": str(e)}


async def generate_insight(asset, metric, timeframe):
    """Generate actionable insights based on the metric and data."""
    # Fetch relevant data from Vybe API
    data = await fetch_from_vybe_api(f"insights/{asset}", {
        "metric": metric,
        "timeframe": timeframe
    })

    if "error" in data:
        return f"Error fetching data: {data['error']}"

    # Process the data based on the metric
    if metric == "price_action":
        return process_price_action(data, asset, timeframe)
    elif metric == "social_sentiment":
        return process_social_sentiment(data, asset, timeframe)
    elif metric == "volume_analysis":
        return process_volume_analysis(data, asset, timeframe)
    elif metric == "funding_rates":
        return process_funding_rates(data, asset, timeframe)
    elif metric == "whale_activity":
        return process_whale_activity(data, asset, timeframe)
    elif metric == "market_dominance":
        return process_market_dominance(data, asset, timeframe)
    elif metric == "volatility_index":
        return process_volatility_index(data, asset, timeframe)
    else:
        return f"Unknown metric: {metric}"


def process_price_action(data, asset, timeframe):
    """Process price action data and generate insight."""
    current_price = data.get("current_price", 0)
    price_change = data.get("price_change_percentage", 0)
    support_level = data.get("support_level", 0)
    resistance_level = data.get("resistance_level", 0)

    signal = "NEUTRAL"
    if price_change > 5:
        signal = "BULLISH"
    elif price_change < -5:
        signal = "BEARISH"

    return {
        "text": f"📊 *{asset} Price Action ({TIMEFRAMES[timeframe]})* 📊\n\n"
                f"Current Price: ${current_price:,.2f}\n"
                f"24h Change: {price_change:.2f}%\n"
                f"Support Level: ${support_level:,.2f}\n"
                f"Resistance Level: ${resistance_level:,.2f}\n\n"
                f"Signal: {signal}\n\n"
                f"*Actionable Insight:*\n"
                f"{'Consider taking profit near resistance levels' if price_change > 0 else 'Watch for potential buy opportunity near support'}\n\n"
                f"View detailed analysis on [AlphaVybe]({ALPHAVYBE_BASE_URL}/asset/{asset})",
        "chart_data": data.get("price_history", []),
        "chart_type": "price"
    }


def process_social_sentiment(data, asset, timeframe):
    """Process social sentiment data and generate insight."""
    sentiment_score = data.get("sentiment_score", 0)  # -100 to 100
    sentiment_change = data.get("sentiment_change", 0)
    twitter_volume = data.get("twitter_volume", 0)
    reddit_volume = data.get("reddit_volume", 0)

    sentiment_status = "Neutral"
    if sentiment_score > 50:
        sentiment_status = "Very Positive"
    elif sentiment_score > 20:
        sentiment_status = "Positive"
    elif sentiment_score < -50:
        sentiment_status = "Very Negative"
    elif sentiment_score < -20:
        sentiment_status = "Negative"

    return {
        "text": f"🔍 *{asset} Social Sentiment ({TIMEFRAMES[timeframe]})* 🔍\n\n"
                f"Sentiment Score: {sentiment_score} ({sentiment_status})\n"
                f"Sentiment Change: {sentiment_change:+.2f}\n"
                f"Twitter Volume: {twitter_volume:,}\n"
                f"Reddit Volume: {reddit_volume:,}\n\n"
                f"*Actionable Insight:*\n"
                f"{'Social sentiment is bullish, suggesting positive momentum may continue' if sentiment_score > 20 else 'Negative sentiment could indicate a potential reversal or continuation of downtrend' if sentiment_score < -20 else 'Neutral sentiment suggests sideways movement may continue'}\n\n"
                f"View detailed sentiment analysis on [AlphaVybe]({ALPHAVYBE_BASE_URL}/asset/{asset}/sentiment)",
        "chart_data": data.get("sentiment_history", []),
        "chart_type": "sentiment"
    }


def process_volume_analysis(data, asset, timeframe):
    """Process volume analysis data and generate insight."""
    current_volume = data.get("current_volume", 0)
    volume_change = data.get("volume_change_percentage", 0)
    avg_volume = data.get("average_volume", 0)

    volume_signal = "NEUTRAL"
    if volume_change > 100:
        volume_signal = "VERY HIGH"
    elif volume_change > 50:
        volume_signal = "HIGH"
    elif volume_change < -50:
        volume_signal = "VERY LOW"
    elif volume_change < -25:
        volume_signal = "LOW"

    return {
        "text": f"📈 *{asset} Volume Analysis ({TIMEFRAMES[timeframe]})* 📈\n\n"
                f"Current Volume: ${current_volume:,.0f}\n"
                f"Volume Change: {volume_change:+.2f}%\n"
                f"Average Volume: ${avg_volume:,.0f}\n\n"
                f"Volume Signal: {volume_signal}\n\n"
                f"*Actionable Insight:*\n"
                f"{'High volume confirms the current trend strength' if volume_change > 25 else 'Low volume suggests caution as current move lacks conviction'}\n\n"
                f"View detailed volume analysis on [AlphaVybe]({ALPHAVYBE_BASE_URL}/asset/{asset}/volume)",
        "chart_data": data.get("volume_history", []),
        "chart_type": "volume"
    }


def process_funding_rates(data, asset, timeframe):
    """Process funding rates data and generate insight."""
    current_rate = data.get("current_funding_rate", 0)
    rate_change = data.get("funding_rate_change", 0)
    avg_rate = data.get("average_funding_rate", 0)

    signal = "NEUTRAL"
    if current_rate > 0.1:
        signal = "EXTREMELY POSITIVE"
    elif current_rate > 0.05:
        signal = "VERY POSITIVE"
    elif current_rate > 0.01:
        signal = "POSITIVE"
    elif current_rate < -0.1:
        signal = "EXTREMELY NEGATIVE"
    elif current_rate < -0.05:
        signal = "VERY NEGATIVE"
    elif current_rate < -0.01:
        signal = "NEGATIVE"

    return {
        "text": f"💰 *{asset} Funding Rates ({TIMEFRAMES[timeframe]})* 💰\n\n"
                f"Current Rate: {current_rate:.4f}%\n"
                f"Rate Change: {rate_change:+.4f}%\n"
                f"Average Rate: {avg_rate:.4f}%\n\n"
                f"Signal: {signal}\n\n"
                f"*Actionable Insight:*\n"
                f"{'Positive funding rates indicate longs are paying shorts, suggesting potential reversal if extended' if current_rate > 0.01 else 'Negative funding rates indicate shorts are paying longs, watch for potential short squeeze'}\n\n"
                f"View detailed derivatives data on [AlphaVybe]({ALPHAVYBE_BASE_URL}/asset/{asset}/derivatives)",
        "chart_data": data.get("funding_history", []),
        "chart_type": "funding"
    }


def process_whale_activity(data, asset, timeframe):
    """Process whale activity data and generate insight."""
    incoming_transfers = data.get("incoming_transfers", 0)
    outgoing_transfers = data.get("outgoing_transfers", 0)
    net_flow = incoming_transfers - outgoing_transfers
    largest_transfer = data.get("largest_transfer", 0)

    signal = "NEUTRAL"
    if net_flow > 10000000:
        signal = "STRONG ACCUMULATION"
    elif net_flow > 1000000:
        signal = "ACCUMULATION"
    elif net_flow < -10000000:
        signal = "STRONG DISTRIBUTION"
    elif net_flow < -1000000:
        signal = "DISTRIBUTION"

    return {
        "text": f"🐋 *{asset} Whale Activity ({TIMEFRAMES[timeframe]})* 🐋\n\n"
                f"Incoming Transfers: ${incoming_transfers:,.0f}\n"
                f"Outgoing Transfers: ${outgoing_transfers:,.0f}\n"
                f"Net Flow: ${net_flow:+,.0f}\n"
                f"Largest Transfer: ${largest_transfer:,.0f}\n\n"
                f"Signal: {signal}\n\n"
                f"*Actionable Insight:*\n"
                f"{'Whales are accumulating, indicating possible bullish outlook' if net_flow > 0 else 'Whales are distributing, be cautious of potential downward pressure'}\n\n"
                f"Track whale movements on [AlphaVybe]({ALPHAVYBE_BASE_URL}/asset/{asset}/whales)",
        "chart_data": data.get("whale_history", []),
        "chart_type": "whales"
    }


def process_market_dominance(data, asset, timeframe):
    """Process market dominance data and generate insight."""
    current_dominance = data.get("current_dominance", 0)
    dominance_change = data.get("dominance_change", 0)
    historical_avg = data.get("historical_average", 0)

    status = "NORMAL"
    if current_dominance > historical_avg * 1.2:
        status = "SIGNIFICANTLY ABOVE AVERAGE"
    elif current_dominance > historical_avg * 1.05:
        status = "ABOVE AVERAGE"
    elif current_dominance < historical_avg * 0.8:
        status = "SIGNIFICANTLY BELOW AVERAGE"
    elif current_dominance < historical_avg * 0.95:
        status = "BELOW AVERAGE"

    return {
        "text": f"👑 *{asset} Market Dominance ({TIMEFRAMES[timeframe]})* 👑\n\n"
                f"Current Dominance: {current_dominance:.2f}%\n"
                f"Dominance Change: {dominance_change:+.2f}%\n"
                f"Historical Average: {historical_avg:.2f}%\n\n"
                f"Status: {status}\n\n"
                f"*Actionable Insight:*\n"
                f"{'Rising market dominance often indicates a flight to quality during uncertain times' if dominance_change > 0 else 'Declining market dominance may signal rotation into altcoins and increased risk appetite'}\n\n"
                f"View market trends on [AlphaVybe]({ALPHAVYBE_BASE_URL}/market/dominance)",
        "chart_data": data.get("dominance_history", []),
        "chart_type": "dominance"
    }


def process_volatility_index(data, asset, timeframe):
    """Process volatility index data and generate insight."""
    current_volatility = data.get("current_volatility", 0)
    volatility_change = data.get("volatility_change", 0)
    historical_volatility = data.get("historical_volatility", 0)

    status = "NORMAL"
    if current_volatility > historical_volatility * 2:
        status = "EXTREMELY HIGH"
    elif current_volatility > historical_volatility * 1.5:
        status = "VERY HIGH"
    elif current_volatility > historical_volatility * 1.2:
        status = "HIGH"
    elif current_volatility < historical_volatility * 0.5:
        status = "EXTREMELY LOW"
    elif current_volatility < historical_volatility * 0.8:
        status = "LOW"

    return {
        "text": f"📉 *{asset} Volatility Index ({TIMEFRAMES[timeframe]})* 📉\n\n"
                f"Current Volatility: {current_volatility:.2f}\n"
                f"Volatility Change: {volatility_change:+.2f}\n"
                f"Historical Volatility: {historical_volatility:.2f}\n\n"
                f"Status: {status}\n\n"
                f"*Actionable Insight:*\n"
                f"{'High volatility signals potential for significant price movement - consider adjusting position sizes' if current_volatility > historical_volatility else 'Low volatility periods often precede major market moves - watch for breakouts'}\n\n"
                f"Analyze volatility patterns on [AlphaVybe]({ALPHAVYBE_BASE_URL}/asset/{asset}/volatility)",
        "chart_data": data.get("volatility_history", []),
        "chart_type": "volatility"
    }


async def generate_chart(data, chart_type, asset):
    """Generate a chart based on the data and chart type."""
    if not data:
        return None

    try:
        # Convert data to pandas DataFrame
        df = pd.DataFrame(data)

        # Create figure
        plt.figure(figsize=(10, 6))

        if chart_type == "price":
            plt.plot(df['timestamp'], df['price'], color='blue')
            plt.title(f"{asset} Price Chart")
            plt.ylabel("Price (USD)")
        elif chart_type == "sentiment":
            plt.plot(df['timestamp'], df['sentiment'], color='green')
            plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
            plt.title(f"{asset} Sentiment Score")
            plt.ylabel("Sentiment (-100 to 100)")
        elif chart_type == "volume":
            plt.bar(df['timestamp'], df['volume'], color='purple', alpha=0.7)
            plt.title(f"{asset} Trading Volume")
            plt.ylabel("Volume (USD)")
        elif chart_type == "funding":
            plt.plot(df['timestamp'], df['rate'], color='orange')
            plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
            plt.title(f"{asset} Funding Rate")
            plt.ylabel("Rate (%)")
        elif chart_type == "whales":
            plt.bar(df['timestamp'], df['net_flow'], color='teal', alpha=0.7)
            plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
            plt.title(f"{asset} Whale Net Flow")
            plt.ylabel("Net Flow (USD)")
        elif chart_type == "dominance":
            plt.plot(df['timestamp'], df['dominance'], color='red')
            plt.title(f"{asset} Market Dominance")
            plt.ylabel("Dominance (%)")
        elif chart_type == "volatility":
            plt.plot(df['timestamp'], df['volatility'], color='magenta')
            plt.title(f"{asset} Volatility Index")
            plt.ylabel("Volatility")

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
        f"Welcome to *VybeInsightBot* - your crypto market intelligence assistant. "
        f"I provide actionable insights using Vybe.fyi data to help you make informed trading decisions.\n\n"
        f"What would you like to explore today?"
    )

    keyboard = [
        [InlineKeyboardButton("🔍 Get Market Insights", callback_data="market_insights")],
        [InlineKeyboardButton("📊 Asset Analysis", callback_data="asset_analysis")],
        [InlineKeyboardButton("🔔 Setup Alerts", callback_data="setup_alerts")],
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
        "*VybeInsightBot Commands:*\n\n"
        "/start - Start the bot and show main menu\n"
        "/help - Show this help message\n"
        "/insights - Get market insights\n"
        "/analysis <asset> - Get analysis for a specific asset\n"
        "/alerts - Setup price and metric alerts\n"
        "/status - Check bot and API status\n\n"

        "*Available Metrics:*\n"
        "• Price Action - Technical analysis and price movements\n"
        "• Social Sentiment - Aggregated social media sentiment\n"
        "• Volume Analysis - Trading volume patterns and anomalies\n"
        "• Funding Rates - Perpetual swap funding rates analysis\n"
        "• Whale Activity - Large wallet transaction monitoring\n"
        "• Market Dominance - Asset's market share tracking\n"
        "• Volatility Index - Price volatility measurements\n\n"

        "For more detailed analytics, visit [AlphaVybe](https://alphavybe.fyi)"
    )

    await update.message.reply_text(help_text, parse_mode='Markdown', disable_web_page_preview=True)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check bot and API status."""
    # Test Vybe API connection
    try:
        api_response = await fetch_from_vybe_api("status")
        api_status = "✅ Online" if not api_response.get("error") else f"❌ Error: {api_response.get('error')}"
    except Exception as e:
        api_status = f"❌ Error: {str(e)}"

    status_text = (
        "*VybeInsightBot Status*\n\n"
        f"Bot Status: ✅ Online\n"
        f"Vybe API: {api_status}\n"
        f"Last Update: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"Supported Assets: {len(TOP_ASSETS)}\n"
        f"Available Metrics: {len(AVAILABLE_METRICS)}"
    )

    await update.message.reply_text(status_text, parse_mode='Markdown')


async def insights_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Triggered by /insights command - show asset selection."""
    return await show_asset_selection(update, context)


async def analysis_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Triggered by /analysis <asset> command."""
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "Please specify an asset symbol. Example: `/analysis BTC`",
            parse_mode='Markdown'
        )
        return

    asset = context.args[0].upper()
    if asset not in TOP_ASSETS:
        await update.message.reply_text(
            f"Asset {asset} not supported. Please choose from the supported assets list.",
            parse_mode='Markdown'
        )
        return

    # Show loading message
    message = await update.message.reply_text("Fetching asset overview...")

    try:
        # Fetch basic asset data
        asset_data = await fetch_from_vybe_api(f"assets/{asset}")

        if "error" in asset_data:
            await message.edit_text(f"Error fetching data: {asset_data['error']}")
            return

        # Process data
        price = asset_data.get("price", 0)
        price_change_24h = asset_data.get("price_change_24h", 0)
        volume_24h = asset_data.get("volume_24h", 0)
        market_cap = asset_data.get("market_cap", 0)

        # Sentiment summary
        sentiment = asset_data.get("sentiment", 0)  # -100 to 100
        sentiment_text = "Neutral"
        if sentiment > 50:
            sentiment_text = "Very Bullish"
        elif sentiment > 20:
            sentiment_text = "Bullish"
        elif sentiment < -50:
            sentiment_text = "Very Bearish"
        elif sentiment < -20:
            sentiment_text = "Bearish"

        # Analysis text
        analysis_text = (
            f"*{asset} Analysis Overview*\n\n"
            f"💰 *Price:* ${price:,.2f} ({price_change_24h:+.2f}%)\n"
            f"📊 *Volume 24h:* ${volume_24h:,.0f}\n"
            f"🏦 *Market Cap:* ${market_cap:,.0f}\n"
            f"🔍 *Sentiment:* {sentiment_text} ({sentiment:.1f})\n\n"
            f"*Select a metric for detailed analysis:*"
        )

        # Keyboard with metrics
        keyboard = []
        for metric_id, metric_name in AVAILABLE_METRICS.items():
            keyboard.append([InlineKeyboardButton(
                metric_name,
                callback_data=f"metric:{asset}:{metric_id}"
            )])

        keyboard.append([InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Update the loading message with the analysis
        await message.edit_text(
            analysis_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        await message.edit_text(f"Error processing data: {str(e)}")


async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Triggered by /alerts command."""
    alerts_text = (
        "*🔔 Alerts Setup*\n\n"
        "Set up custom alerts to be notified when specific conditions are met. "
        "Alerts can be based on price movements, sentiment changes, and other metrics.\n\n"
        "Select the type of alert you want to set up:"
    )

    keyboard = [
        [InlineKeyboardButton("💰 Price Alert", callback_data="alert_price")],
        [InlineKeyboardButton("📊 Metric Alert", callback_data="alert_metric")],
        [InlineKeyboardButton("🐋 Whale Alert", callback_data="alert_whale")],
        [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        alerts_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


# Callback Query Handlers
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button press."""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "market_insights":
        return await show_market_insights(update, context)
    elif data == "asset_analysis":
        return await show_asset_selection(update, context)
    elif data == "setup_alerts":
        await show_alerts_setup(update, context)
        return MAIN_MENU
    elif data == "help":
        await show_help(update, context)
        return MAIN_MENU
    elif data == "back_to_main":
        return await show_main_menu(update, context)
    elif data.startswith("asset:"):
        _, asset = data.split(":")
        context.user_data["selected_asset"] = asset
        return await show_timeframe_selection(update, context)
    elif data.startswith("timeframe:"):
        _, timeframe = data.split(":")
        context.user_data["selected_timeframe"] = timeframe
        return await show_metric_selection(update, context)
    elif data.startswith("metric:"):
        parts = data.split(":")
        if len(parts) == 3:
            _, asset, metric = parts
            context.user_data["selected_asset"] = asset
            context.user_data["selected_metric"] = metric
            await show_metric_analysis(update, context)
        else:
            _, metric = parts
            context.user_data["selected_metric"] = metric
            await show_analysis_result(update, context)
        return MAIN_MENU
    elif data.startswith("alert_"):
        alert_type = data[6:]  # Remove "alert_" prefix
        await show_alert_setup(update, context, alert_type)
        return MAIN_MENU

    return MAIN_MENU


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the main menu."""
    keyboard = [
        [InlineKeyboardButton("🔍 Get Market Insights", callback_data="market_insights")],
        [InlineKeyboardButton("📊 Asset Analysis", callback_data="asset_analysis")],
        [InlineKeyboardButton("🔔 Setup Alerts", callback_data="setup_alerts")],
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


async def show_market_insights(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show market insights overview."""
    query = update.callback_query

    # Show loading message
    await query.edit_message_text("Fetching market insights...")

    try:
        # Fetch market overview
        market_data = await fetch_from_vybe_api("market/overview")

        if "error" in market_data:
            await query.edit_message_text(f"Error fetching market data: {market_data['error']}")
            return MAIN_MENU

        # Process data
        total_market_cap = market_data.get("total_market_cap", 0)
        market_cap_change = market_data.get("market_cap_change_24h", 0)
        total_volume = market_data.get("total_volume_24h", 0)
        btc_dominance = market_data.get("btc_dominance", 0)
        eth_dominance = market_data.get("eth_dominance", 0)
        fear_greed_index = market_data.get("fear_greed_index", 50)  # 0-100
        active_addresses = market_data.get("active_addresses_24h", 0)

        # Format market overview text
        fear_greed_text = "Neutral"
        if fear_greed_index >= 75:
            fear_greed_text = "Extreme Greed"
        elif fear_greed_index >= 60:
            fear_greed_text = "Greed"
        elif fear_greed_index <= 25:
            fear_greed_text = "Extreme Fear"
        elif fear_greed_index <= 40:
            fear_greed_text = "Fear"

        market_text = (
            f"*Crypto Market Overview*\n\n"
            f"💰 *Total Market Cap:* ${total_market_cap:,.0f} ({market_cap_change:+.2f}%)\n"
            f"📊 *24h Volume:* ${total_volume:,.0f}\n"
            f"🔶 *BTC Dominance:* {btc_dominance:.2f}%\n"
            f"🔷 *ETH Dominance:* {eth_dominance:.2f}%\n"
            f"😨 *Fear & Greed Index:* {fear_greed_index} - {fear_greed_text}\n"
            f"👥 *Active Addresses (24h):* {active_addresses:,}\n\n"
            f"*Top Trending Assets:*\n"
        )

        # Add trending assets
        trending_assets = market_data.get("trending_assets", [])
        for i, asset in enumerate(trending_assets[:5], 1):
            symbol = asset.get("symbol", "")
            price = asset.get("price", 0)
            change = asset.get("price_change_24h", 0)
            market_text += f"{i}. {symbol}: ${price:,.2f} ({change:+.2f}%)\n"

        market_text += "\n*Select an option:*"

        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("View Detailed Market Stats", callback_data="market_stats")],
            [InlineKeyboardButton("Top Gainers", callback_data="top_gainers"),
             InlineKeyboardButton("Top Losers", callback_data="top_losers")],
            [InlineKeyboardButton("Analyze Specific Asset", callback_data="asset_analysis")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            market_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        await query.edit_message_text(f"Error processing market data: {str(e)}")

    return MAIN_MENU


async def show_asset_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show asset selection buttons."""
    message = "Select an asset to analyze:"

    # Create a keyboard with 3 assets per row
    keyboard = []
    row = []
    for i, asset in enumerate(TOP_ASSETS):
        row.append(InlineKeyboardButton(asset, callback_data=f"asset:{asset}"))
        if (i + 1) % 3 == 0 or i == len(TOP_ASSETS) - 1:
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

    return ASSET_SELECTION


async def show_timeframe_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show timeframe selection buttons."""
    asset = context.user_data.get("selected_asset", "")
    message = f"Select timeframe for {asset} analysis:"

    keyboard = []
    for timeframe_id, timeframe_name in TIMEFRAMES.items():
        keyboard.append([InlineKeyboardButton(timeframe_name, callback_data=f"timeframe:{timeframe_id}")])

    keyboard.append([InlineKeyboardButton("Back", callback_data="asset_analysis")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup
    )

    return TIMEFRAME_SELECTION


async def show_metric_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show metric selection buttons."""
    asset = context.user_data.get("selected_asset", "")
    timeframe = context.user_data.get("selected_timeframe", "")
    timeframe_name = TIMEFRAMES.get(timeframe, "")

    message = f"Select metric for {asset} ({timeframe_name}):"

    keyboard = []
    for metric_id, metric_name in AVAILABLE_METRICS.items():
        keyboard.append([InlineKeyboardButton(metric_name, callback_data=f"metric:{metric_id}")])

    keyboard.append([InlineKeyboardButton("Back", callback_data=f"asset:{asset}")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup
    )

    return METRIC_SELECTION


async def show_analysis_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show analysis result based on selected options."""
    query = update.callback_query

    asset = context.user_data.get("selected_asset", "")
    timeframe = context.user_data.get("selected_timeframe", "")
    metric = context.user_data.get("selected_metric", "")

    # Show loading message
    await query.edit_message_text(f"Analyzing {asset} {AVAILABLE_METRICS[metric]} data...")

    try:
        # Generate insights
        insight = await generate_insight(asset, metric, timeframe)

        if isinstance(insight, str):
            # Error message
            await query.edit_message_text(insight)
            return

        # Send chart if available
        if "chart_data" in insight and "chart_type" in insight:
            chart_buffer = await generate_chart(insight["chart_data"], insight["chart_type"], asset)
            if chart_buffer:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=chart_buffer,
                    caption=f"{asset} {AVAILABLE_METRICS[metric]} Chart"
                )

        # Send analysis text
        keyboard = [
            [InlineKeyboardButton("View on AlphaVybe", url=f"{ALPHAVYBE_BASE_URL}/asset/{asset}")],
            [InlineKeyboardButton("New Analysis", callback_data="asset_analysis")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            insight["text"],
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    except Exception as e:
        await query.edit_message_text(f"Error analyzing data: {str(e)}")


async def show_metric_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show metric analysis for direct metric selection."""
    query = update.callback_query

    asset = context.user_data.get("selected_asset", "")
    metric = context.user_data.get("selected_metric", "")

    # Default to 1d timeframe
    timeframe = "1d"

    # Show loading message
    await query.edit_message_text(f"Analyzing {asset} {AVAILABLE_METRICS[metric]} data...")

    try:
        # Generate insights
        insight = await generate_insight(asset, metric, timeframe)

        if isinstance(insight, str):
            # Error message
            await query.edit_message_text(insight)
            return

        # Send chart if available
        if "chart_data" in insight and "chart_type" in insight:
            chart_buffer = await generate_chart(insight["chart_data"], insight["chart_type"], asset)
            if chart_buffer:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=chart_buffer,
                    caption=f"{asset} {AVAILABLE_METRICS[metric]} Chart"
                )

        # Send analysis text
        keyboard = [
            [InlineKeyboardButton("View on AlphaVybe", url=f"{ALPHAVYBE_BASE_URL}/asset/{asset}")],
            [InlineKeyboardButton("New Analysis", callback_data="asset_analysis")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            insight["text"],
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    except Exception as e:
        await query.edit_message_text(f"Error analyzing data: {str(e)}")


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help information."""
    query = update.callback_query

    help_text = (
        "*VybeInsightBot Help*\n\n"
        "This bot provides real-time crypto insights using Vybe APIs. Here's how to use it:\n\n"

        "*Main Features:*\n"
        "• *Market Insights* - Get an overview of crypto market conditions\n"
        "• *Asset Analysis* - Analyze specific assets using various metrics\n"
        "• *Alerts* - Set up notifications for price movements and other events\n\n"

        "*Available Commands:*\n"
        "/start - Start the bot and show main menu\n"
        "/help - Show this help message\n"
        "/insights - Get market insights\n"
        "/analysis <asset> - Get analysis for a specific asset\n"
        "/alerts - Setup price and metric alerts\n"
        "/status - Check bot and API status\n\n"

        "*Supported Metrics:*\n"
        "• Price Action - Technical analysis and price movements\n"
        "• Social Sentiment - Aggregated social media sentiment\n"
        "• Volume Analysis - Trading volume patterns\n"
        "• Funding Rates - Perpetual swap funding rates\n"
        "• Whale Activity - Large wallet transactions\n"
        "• Market Dominance - Asset's market share\n"
        "• Volatility Index - Price volatility measurements\n\n"

        "For more detailed analytics, visit [AlphaVybe](https://alphavybe.fyi)"
    )

    keyboard = [[InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        help_text,
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )


async def show_alerts_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show alerts setup options."""
    query = update.callback_query

    alerts_text = (
        "*🔔 Alerts Setup*\n\n"
        "Set up custom alerts to be notified when specific conditions are met. "
        "Select the type of alert you want to set up:"
    )

    keyboard = [
        [InlineKeyboardButton("💰 Price Alert", callback_data="alert_price")],
        [InlineKeyboardButton("📊 Metric Alert", callback_data="alert_metric")],
        [InlineKeyboardButton("🐋 Whale Alert", callback_data="alert_whale")],
        [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        alerts_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def show_alert_setup(update: Update, context: ContextTypes.DEFAULT_TYPE, alert_type: str) -> None:
    """Show setup form for specific alert type."""
    query = update.callback_query

    if alert_type == "price":
        alert_setup_text = (
            "*💰 Price Alert Setup*\n\n"
            "To set up a price alert, use the following format:\n"
            "`/setalert BTC price above 50000`\n"
            "`/setalert ETH price below 3000`\n\n"
            "You'll receive a notification when the condition is met."
        )
    elif alert_type == "metric":
        alert_setup_text = (
            "*📊 Metric Alert Setup*\n\n"
            "To set up a metric alert, use the following format:\n"
            "`/setalert BTC sentiment above 50`\n"
            "`/setalert ETH volume increase 30%`\n\n"
            "Available metrics: sentiment, volume, funding, volatility"
        )
    elif alert_type == "whale":
        alert_setup_text = (
            "*🐋 Whale Alert Setup*\n\n"
            "To set up a whale transaction alert, use the following format:\n"
            "`/setalert BTC whale above 5000000`\n"
            "`/setalert ETH whale any`\n\n"
            "You'll be notified of significant whale movements."
        )
    else:
        alert_setup_text = "Invalid alert type."

    keyboard = [[InlineKeyboardButton("Back", callback_data="setup_alerts")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        alert_setup_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


def main():
    """Start the bot."""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("insights", insights_command),
        ],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(button_callback),
            ],
            ASSET_SELECTION: [
                CallbackQueryHandler(button_callback),
            ],
            TIMEFRAME_SELECTION: [
                CallbackQueryHandler(button_callback),
            ],
            METRIC_SELECTION: [
                CallbackQueryHandler(button_callback),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)

    # Add standalone command handlers
    # application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("analysis", analysis_command))
    application.add_handler(CommandHandler("alerts", alerts_command))

    # Start the Bot
    application.run_polling()


if __name__ == "__main__":
    main()