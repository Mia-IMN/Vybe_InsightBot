# Vybe_InsightBot

A powerful Telegram bot that provides actionable, real-time crypto insights using Vybe.fyi APIs. This bot helps traders make informed decisions by delivering market intelligence, asset analysis, and customizable alerts directly in Telegram.

![VybeInsightBot Banner](/vybelogo360x360.jpg)

## 🚀 Features

- **Real-time Market Insights**: Get comprehensive market overviews including market cap, volume, BTC dominance, and Fear & Greed Index.
- **Multi-dimensional Asset Analysis**: Analyze crypto assets across 7 different metrics:
  - Price Action
  - Social Sentiment
  - Volume Analysis
  - Funding Rates
  - Whale Activity
  - Market Dominance
  - Volatility Index
- **Data Visualization**: Automatically generated charts for each analysis type.
- **Customizable Alerts**: Set up notifications for price movements, metric thresholds, and whale activity.
- **AlphaVybe Integration**: Direct links to AlphaVybe platform for deeper analysis.
- **User-friendly Navigation**: Intuitive interface with button-based navigation.

## 📋 Requirements

- Python 3.8+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Vybe API Key (from [Vybe.fyi](https://vybe.fyi))
- Libraries: python-telegram-bot, aiohttp, pandas, matplotlib, etc.

## 🔧 Installation

1. **Clone the repository**

```bash
git clone https://github.com/Mia-IMN/Vybe_InsightBot.git
cd Vybe_InsightBot
```

2. **Create and activate a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create a `.env` file in the project root with the following:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
VYBE_API_KEY=your_vybe_api_key
```

5. **Run the bot**

```bash
python Vybe_InsightBot.py
```

## 📊 Metrics Explained

### Price Action
Technical analysis of price movements, support/resistance levels, and trend signals.

**Example output:**
```
📊 BTC Price Action (1 Day) 📊

Current Price: $63,245.78
24h Change: +2.35%
Support Level: $61,500.00
Resistance Level: $64,800.00

Signal: BULLISH

Actionable Insight:
Consider taking profit near resistance levels
```

### Social Sentiment
Aggregated sentiment analysis from social media platforms like Twitter and Reddit.

**Example output:**
```
🔍 ETH Social Sentiment (4 Hours) 🔍

Sentiment Score: 68 (Very Positive)
Sentiment Change: +12.50
Twitter Volume: 25,380
Reddit Volume: 8,742

Actionable Insight:
Social sentiment is bullish, suggesting positive momentum may continue
```

### Volume Analysis
Examination of trading volume patterns, anomalies, and signals.

**Example output:**
```
📈 SOL Volume Analysis (1 Day) 📈

Current Volume: $985,245,600
Volume Change: +72.35%
Average Volume: $572,320,450

Volume Signal: HIGH

Actionable Insight:
High volume confirms the current trend strength
```

### Funding Rates
Analysis of perpetual swap funding rates across major exchanges.

**Example output:**
```
💰 BNB Funding Rates (4 Hours) 💰

Current Rate: 0.0125%
Rate Change: +0.0032%
Average Rate: 0.0085%

Signal: POSITIVE

Actionable Insight:
Positive funding rates indicate longs are paying shorts, suggesting potential reversal if extended
```

### Whale Activity
Monitoring of large wallet transactions and fund movements.

**Example output:**
```
🐋 XRP Whale Activity (1 Day) 🐋

Incoming Transfers: $25,320,500
Outgoing Transfers: $12,250,300
Net Flow: +$13,070,200
Largest Transfer: $5,230,000

Signal: ACCUMULATION

Actionable Insight:
Whales are accumulating, indicating possible bullish outlook
```

### Market Dominance
Tracking an asset's market share and its changes over time.

**Example output:**
```
👑 BTC Market Dominance (7 Days) 👑

Current Dominance: 48.32%
Dominance Change: -0.75%
Historical Average: 52.15%

Status: BELOW AVERAGE

Actionable Insight:
Declining market dominance may signal rotation into altcoins and increased risk appetite
```

### Volatility Index
Measurement of price volatility and its deviation from historical norms.

**Example output:**
```
📉 ADA Volatility Index (1 Day) 📉

Current Volatility: 2.35
Volatility Change: +0.45
Historical Volatility: 1.85

Status: HIGH

Actionable Insight:
High volatility signals potential for significant price movement - consider adjusting position sizes
```

## 🔔 Setting Up Alerts

You can set up three types of alerts:

### Price Alerts
```
/setalert BTC price above 70000
/setalert ETH price below 3500
```

### Metric Alerts
```
/setalert SOL sentiment above 60
/setalert ADA volume increase 35%
```

### Whale Alerts
```
/setalert XRP whale above 10000000
/setalert LINK whale any
```

## 📝 Bot Commands

- `/start` - Start the bot and show main menu
- `/help` - Show help information
- `/insights` - Get market insights
- `/analysis <asset>` - Get analysis for a specific asset
- `/alerts` - Setup price and metric alerts
- `/status` - Check bot and API status

## 🌐 AlphaVybe Integration

VybeInsightBot seamlessly integrates with [AlphaVybe](https://alphavybe.fyi) for more detailed analysis. Each insight comes with a direct link to the relevant asset or metric page on AlphaVybe platform.

## 🔄 How It's Different from PhanesBot

VybeInsightBot improves upon PhanesBot in several key ways:

1. **Multi-dimensional Analysis**: Provides 7 different metrics compared to PhanesBot's limited feature set.
2. **Visual Data Representation**: Automatically generates charts for better understanding.
3. **Actionable Insights**: Each analysis comes with specific trading suggestions.
4. **Customizable Alerts**: More flexible alert system with multiple trigger conditions.
5. **Deeper API Integration**: Full utilization of Vybe.fyi API capabilities.
6. **Improved User Experience**: Intuitive button-based navigation system.

[//]: # (## 📱 Screenshots)

[//]: # ()
[//]: # (![Market Overview]&#40;&#41;)

[//]: # (![Asset Analysis]&#40;&#41;)

[//]: # (![Alert Setup]&#40;&#41;)

## 🧩 Project Structure

```
vybeinsightbot/
├── vybeinsightbot.py       # Main bot file
├── requirements.txt        # Required dependencies
├── .env                    # Environment variables (not in repo)
├── README.md               # Documentation
└── assets/                 # Images and other assets
```

## 📄 License

MIT License

## 👨‍💻 Contributors

- Mia Ikechukwu - Initial work

## 🔗 Links

- [Vybe.fyi](https://vybe.fyi) - API provider
- [AlphaVybe](https://alphavybe.fyi) - Advanced analytics platform