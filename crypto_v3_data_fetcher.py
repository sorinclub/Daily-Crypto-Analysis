# crypto_v3_data_fetcher.py
import requests
import json
import time
import os

# Telegram configuration from environment variables
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']  
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

def send_to_telegram(message):
    """Sends message to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Message sent to Telegram!")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

def fetch_fear_greed_index():
    """Fetches Fear & Greed Index from Alternative.me"""
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['data']:
            fng = data['data'][0]
            return {
                'value': int(fng['value']),
                'sentiment': fng['value_classification']
            }
    except Exception as e:
        print(f"Warning: Could not fetch Fear & Greed Index: {e}")
        return {'value': 'N/A', 'sentiment': 'N/A'}

def fetch_btc_dominance():
    """Fetches BTC Dominance from CoinGecko"""
    try:
        url = "https://api.coingecko.com/api/v3/global"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data:
            market_cap_percentage = data['data']['market_cap_percentage']
            return round(market_cap_percentage.get('btc', 0), 1)
    except Exception as e:
        print(f"Warning: Could not fetch BTC Dominance: {e}")
        return 'N/A'

def fetch_crypto_data():
    """Fetches top 200 coins and sends to Telegram"""
    
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 200,
        'page': 1,
        'sparkline': False,
        'price_change_percentage': '24h'
    }
    
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        # Fetch macro data
        fng = fetch_fear_greed_index()
        btc_dom = fetch_btc_dominance()
        
        # Build message
        message = f"🔷 *V3 DATA READY*\n"
        message += f"`{time.strftime('%Y-%m-%d %H:%M:%S UTC')}`\n\n"
        message += "*Macro:*\n"
        message += f"Fear & Greed: *{fng['value']}* ({fng['sentiment']})\n"
        message += f"BTC Dominance: *{btc_dom}%*\n\n"
        
        # Top 5 coins summary
        message += "*Top 5:*\n"
        for i, coin in enumerate(data[:5], 1):
            symbol = coin['symbol'].upper()
            price = coin['current_price']
            change_24h = coin['price_change_percentage_24h'] or 0
            
            if price < 0.01:
                price_str = f"${price:.6f}"
            else:
                price_str = f"${price:.2f}"
            
            message += f"{i}. {symbol} {price_str} ({change_24h:+.2f}%)\n"
        
        # High momentum coins
        message += "\n*High Momentum (>5%):*\n"
        momentum_count = 0
        for coin in data[20:200]:
            change = coin['price_change_percentage_24h'] or 0
            if abs(change) > 5:
                symbol = coin['symbol'].upper()
                change_str = f"{change:+.2f}%"
                message += f"{symbol} {change_str}\n"
                momentum_count += 1
                if momentum_count >= 5:  # Limit to 5 for brevity
                    break
        
        # Your watchlist (edit this list!)
        watchlist = ['DOT', 'CAKE', 'TIA', 'CRV', 'AVAX', 'ALGO', 'ARB', 'CHZ', 'THETA', '1INCH', 'ICP']
       
        
        message += f"\n*Your Watchlist:*\n"
        watchlist_found = 0
        for coin in data[20:200]:
            if coin['symbol'].upper() in watchlist:
                symbol = coin['symbol'].upper()
                price = coin['current_price']
                change_24h = coin['price_change_percentage_24h'] or 0
                
                if price < 0.01:
                    price_str = f"${price:.6f}"
                else:
                    price_str = f"${price:.2f}"
                
                message += f"{symbol} {price_str} ({change_24h:+.2f}%)\n"
                watchlist_found += 1
        
        # Add command prompt
        message += "\n*Next step:*\nForward this to AI with:\n`Run V3 analysis on this data`"
        
        # Send to Telegram
        send_to_telegram(message)
        
        # Also print for local log
        print(message)
        
    except requests.exceptions.Timeout:
        print("Error: API timeout - try again in 30 seconds")
    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":

    fetch_crypto_data()
