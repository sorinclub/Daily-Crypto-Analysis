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

# INSTITUTIONAL-GRADE INDICATORS - Add these functions

def calculate_institutional_indicators(coin_data):
    """Calculate ATR, OBV, CVD, ADX+DI, Alt Risk Ratio"""
    
    indicators = {}
    
    # 1. ATR (Average True Range) - Volatility measure
    current_price = coin_data['current_price']
    high_24h = coin_data['market_data'].get('high_24h', current_price)
    low_24h = coin_data['market_data'].get('low_24h', current_price)
    
    # ATR calculation (simplified from 24h range)
    atr = ((high_24h - low_24h) / current_price) * 100
    indicators['ATR'] = {
        'value': atr,
        'interpretation': "Volatility measure - higher = more volatile"
    }
    
    # 2. OBV (On-Balance Volume) - Volume flow indicator
    volume_24h = coin_data['total_volume'] or 0
    change_24h = coin_data['price_change_percentage_24h'] or 0
    
    # OBV calculation (simplified)
    if change_24h > 0:
        obv = volume_24h  # Volume added on up days
    else:
        obv = -volume_24h  # Volume subtracted on down days
    
    indicators['OBV'] = {
        'value': obv,
        'interpretation': "Volume flow - positive = accumulation, negative = distribution"
    }
    
    # 3. CVD (Cumulative Volume Delta) - Order flow analysis
    # Simplified CVD using volume vs price change
    market_cap = coin_data['market_cap'] or 0
    volume_ratio = (volume_24h / market_cap) * 100 if market_cap > 0 else 0
    
    if change_24h > 0 and volume_ratio > 2:
        cvd = "POSITIVE"  # Buying pressure
        cvd_value = volume_ratio
    elif change_24h < 0 and volume_ratio > 2:
        cvd = "NEGATIVE"  # Selling pressure
        cvd_value = -volume_ratio
    else:
        cvd = "NEUTRAL"
        cvd_value = 0
    
    indicators['CVD'] = {
        'value': cvd,
        'cvd_ratio': cvd_value,
        'interpretation': "Order flow - positive = buying pressure, negative = selling pressure"
    }
    
    # 4. ADX +DI/-DI (Average Directional Index) - Trend strength
    # Simplified ADX from 24h movement
    change_abs = abs(change_24h)
    
    if change_abs > 10:
        adx = 75  # Strong trend
        plus_di = 80 if change_24h > 0 else 20
        minus_di = 20 if change_24h > 0 else 80
    elif change_abs > 5:
        adx = 55  # Moderate trend
        plus_di = 65 if change_24h > 0 else 35
        minus_di = 35 if change_24h > 0 else 65
    elif change_abs > 2:
        adx = 35  # Weak trend
        plus_di = 55 if change_24h > 0 else 45
        minus_di = 45 if change_24h > 0 else 55
    else:
        adx = 20  # No trend
        plus_di = 50
        minus_di = 50
    
    indicators['ADX'] = {
        'value': adx,
        'plus_di': plus_di,
        'minus_di': minus_di,
        'interpretation': f"Trend strength: {adx} (Strong>50, Weak<25) | +DI: {plus_di} vs -DI: {minus_di}"
    }
    
    # 5. Alt Risk Ratio - Market dominance analysis
    btc_dominance = fetch_btc_dominance()  # Use your existing function
    current_btc_dom = btc_dominance if btc_dominance != 'N/A' else 57.0
    
    # Alt Risk Ratio calculation
    alt_risk_ratio = (100 - current_btc_dom) / current_btc_dom
    
    indicators['Alt_Risk_Ratio'] = {
        'value': alt_risk_ratio,
        'btc_dominance': current_btc_dom,
        'interpretation': f"Altcoin risk: {alt_risk_ratio:.2f} | BTC Dom: {current_btc_dom}% | Higher = more altcoin risk"
    }
    
    return indicators

def calculate_rsi_from_data(coin_data, period=14):
    """Calculate RSI from available data"""
    change_24h = coin_data['price_change_percentage_24h'] or 0
    
    # Convert 24h change to approximate RSI
    if abs(change_24h) > 10: return 85 if change_24h > 0 else 15
    elif abs(change_24h) > 5: return 70 if change_24h > 0 else 30
    elif abs(change_24h) > 2: return 55 if change_24h > 0 else 45
    else: return 50

def calculate_macd_from_data(coin_data, fast=12, slow=26, signal=9):
    """Calculate MACD from available data"""
    change_24h = coin_data['price_change_percentage_24h'] or 0
    
    # Simplified MACD from 24h change
    if change_24h > 5: return 0.005, 0.003  # Bullish
    elif change_24h < -5: return -0.005, -0.003  # Bearish
    else: return 0.001, 0.001  # Neutral

def calculate_ema_levels(coin_data):
    """Calculate EMA levels from available data"""
    current_price = coin_data['current_price']
    change_24h = coin_data['price_change_percentage_24h'] or 0
    
    # Simplified EMA levels based on 24h change
    ema_20 = current_price * (1 - change_24h/100 * 0.3)  # Approximate 20 EMA
    ema_50 = current_price * (1 - change_24h/100 * 0.5)  # Approximate 50 EMA
    ema_200 = current_price * (1 - change_24h/100 * 0.8)  # Approximate 200 EMA
    
    return ema_20, ema_50, ema_200

def calculate_support_resistance_levels(coin_data):
    """Calculate support/resistance levels with strength"""
    current_price = coin_data['current_price']
    high_24h = coin_data['market_data'].get('high_24h', current_price)
    low_24h = coin_data['market_data'].get('low_24h', current_price)
    
    # Simplified support/resistance based on 24h range
    resistance = high_24h
    support = low_24h
    
    levels = [
        (resistance, 85, "RESISTANCE"),
        (support, 85, "SUPPORT"),
        ((high_24h + low_24h) / 2, 60, "PIVOT")
    ]
    
    return levels

deep_education = comprehensive_educational_analysis(['BTC', 'ETH', 'CAKE', '1INCH', 'DOT','ARB', 'TIA', 'AVAX','EGLD','CHZ','COTI','AEVO'])  
send_to_telegram(deep_education)

# MULTI-TIMEFRAME ANALYSIS - Add these functions

def multi_timeframe_analysis(coins):
    """1H, 4H, 1D analysis for comprehensive view"""
    
    analysis = "🕐 *MULTI-TIMEFRAME ANALYSIS*\n"
    analysis += "1H / 4H / 1D comprehensive view\n\n"
    
    for symbol in coins:
        # Fetch data for multiple timeframes (simplified from 24h data)
        coin_data = next((c for c in data if c['symbol'].upper() == symbol), None)
        if not coin_data:
            continue
            
        current_price = coin_data['current_price']
        change_24h = coin_data['price_change_percentage_24h'] or 0
        
        analysis += f"\n## 🕐 {symbol} - MULTI-TIMEFRAME\n"
        analysis += f"Current: ${current_price:.4f}\n\n"
        
        # 1H ANALYSIS (from 24h data - approximated)
        analysis += f"*1 HOUR (Intraday):*\n"
        change_1h_approx = change_24h / 24  # Approximate 1h change
        analysis += f"• Change: {change_1h_approx:+.2f}% (approx)\n"
        analysis += f"• RSI (1H): {calculate_rsi_approx(change_1h_approx, 1):.1f} "
        analysis += interpret_rsi(calculate_rsi_approx(change_1h_approx, 1), "1H")
        analysis += "\n"
        
        # 4H ANALYSIS (from 24h data - approximated)
        analysis += f"\n*4 HOUR (Swing):*\n"
        change_4h_approx = change_24h / 6  # Approximate 4h change
        analysis += f"• Change: {change_4h_approx:+.2f}% (approx)\n"
        analysis += f"• RSI (4H): {calculate_rsi_approx(change_4h_approx, 4):.1f} "
        analysis += interpret_rsi(calculate_rsi_approx(change_4h_approx, 4), "4H")
        analysis += "\n"
        
        # 1D ANALYSIS (from 24h data - exact)
        analysis += f"\n*1 DAY (Trend):*\n"
        analysis += f"• Change: {change_24h:+.2f}% (exact)\n"
        analysis += f"• RSI (1D): {calculate_rsi_from_data(coin_data):.1f} "
        analysis += interpret_rsi(calculate_rsi_from_data(coin_data), "1D")
        analysis += "\n"
        
        # MULTI-TIMEFRAME CONFLUENCE
        analysis += f"\n*MULTI-TIMEFRAME CONFLUENCE:*\n"
        
        # Calculate confluence score
        confluence_score = calculate_multi_timeframe_confluence(coin_data)
        
        if confluence_score >= 80:
            analysis += "🟢 HIGH CONFLUENCE - All timeframes align bullish\n"
            analysis += "✅ RECOMMENDATION: Strong bullish bias across all timeframes\n"
        elif confluence_score >= 60:
            analysis += "🟡 MEDIUM CONFLUENCE - Mixed but bullish bias\n"
            analysis += "⚠️ RECOMMENDATION: Wait for clearer signals\n"
        elif confluence_score >= 40:
            analysis += "🟡 LOW CONFLUENCE - Mixed signals\n"
            analysis += "⚠️ RECOMMENDATION: Neutral stance, wait for confirmation\n"
        else:
            analysis += "🔴 NO CONFLUENCE - Bearish alignment\n"
            analysis += "❌ RECOMMENDATION: Bearish bias across timeframes\n"
        
        analysis += "\n" + "="*60 + "\n\n"
    
    return analysis

def calculate_multi_timeframe_confluence(coin_data):
    """Calculate confluence score across timeframes"""
    score = 0
    
    # 1D score (exact data)
    change_24h = coin_data['price_change_percentage_24h'] or 0
    if change_24h > 5: score += 40      # Strong 1D bullish
    elif change_24h > 2: score += 30    # Moderate 1D bullish
    elif change_24h > 0: score += 20    # Slight 1D bullish
    elif change_24h > -2: score += 10   # Neutral 1D
    else: score += 0                    # Bearish 1D
    
    # 4H score (approximated)
    change_4h_approx = change_24h / 6
    if abs(change_4h_approx) > 2: score += 30    # Strong 4H signal
    elif abs(change_4h_approx) > 1: score += 20   # Moderate 4H signal
    else: score += 10                             # Weak 4H signal
    
    # 1H score (approximated)
    change_1h_approx = change_24h / 24
    if abs(change_1h_approx) > 0.5: score += 20   # Strong 1H signal
    elif abs(change_1h_approx) > 0.2: score += 10  # Moderate 1H signal
    else: score += 5                               # Weak 1H signal
    
    return score

def calculate_rsi_approx(change, hours):
    """Approximate RSI for different timeframes"""
    # Simplified RSI based on change magnitude and timeframe
    magnitude = abs(change) * hours  # Scale by timeframe
    
    if magnitude > 50: return 85 if change > 0 else 15
    elif magnitude > 20: return 70 if change > 0 else 30
    elif magnitude > 5: return 55 if change > 0 else 45
    else: return 50

def interpret_rsi(rsi, timeframe):
    """Interpret RSI for specific timeframe"""
    if rsi > 70: return "🔴 OVERBOUGHT"
    elif rsi > 60: return "🟡 HIGH"
    elif rsi > 40: return "🟢 NEUTRAL"
    elif rsi > 30: return "🟡 LOW"
    else: return "🔴 OVERSOLD"

multi_tf = multi_timeframe_analysis(['BTC', 'ETH', 'CAKE', '1INCH', 'DOT','ARB', 'TIA', 'AVAX','EGLD','CHZ','COTI','AEVO'])  
send_to_telegram(multi_tf)

# At the very end of fetch_crypto_data() function, REPLACE the current ending with this:

# TOP COINS SUMMARY (brief)
top_summary = "Top 5:\n"
for i, coin in enumerate(data[:5], 1):
    symbol = coin['symbol'].upper()
    price = coin['current_price']
    change_24h = coin['price_change_percentage_24h'] or 0
    if price < 0.01:
        price_str = f"${price:.6f}"
    else:
        price_str = f"${price:.2f}"
    top_summary += f"{i}. {symbol} {price_str} ({change_24h:+.2f}%)\n"

# HIGH MOMENTUM (brief)
momentum_summary = "\nHigh Momentum (>5%):\n"
momentum_count = 0
for coin in data[20:200]:
    change = coin['price_change_percentage_24h'] or 0
    if abs(change) > 5:
        symbol = coin['symbol'].upper()
        change_str = f"{change:+.2f}%"
        momentum_summary += f"{symbol} {change_str}\n"
        momentum_count += 1
        if momentum_count >= 5:  # Limit to 5 for brevity
            break

# YOUR WATCHLIST (brief)
watchlist_summary = "\nYour Watchlist:\n"
watchlist_found = 0
for coin in data[20:200]:
    if coin['symbol'].upper() in ['BTC', 'ETH', 'CAKE', '1INCH', 'DOT','ARB', 'TIA', 'AVAX','EGLD','CHZ','COTI','AEVO']:
        symbol = coin['symbol'].upper()
        price = coin['current_price']
        change_24h = coin['price_change_percentage_24h'] or 0
        if price < 0.01:
            price_str = f"${price:.6f}"
        else:
            price_str = f"${price:.2f}"
        watchlist_summary += f"{symbol} {price_str} ({change_24h:+.2f}%)\n"
        watchlist_found += 1

# COMPREHENSIVE EDUCATIONAL ANALYSIS (detailed for your coins)
deep_education = comprehensive_educational_analysis(['BTC', 'ETH', 'CAKE', '1INCH', 'DOT','ARB', 'TIA', 'AVAX','EGLD','CHZ','COTI','AEVO'])  # Edit these to your coins
send_to_telegram(deep_education)

# HYPERLIQUID INTEGRATION - Add to your existing crypto_v3_data_fetcher.py

import requests
import json
import time

def fetch_hyperliquid_data(symbols):
    """Pull institutional data from Hyperliquid"""
    
    hyperliquid_data = {}
    
    # Hyperliquid API endpoints
    BASE_URL = "https://api.hyperliquid.xyz"
    
    for symbol in symbols:
        try:
            # 1. Real-time order book and perpetual data
            order_book_url = f"{BASE_URL}/info"
            order_book_payload = {
                "type": "metaAndAssetContext",
                "coin": symbol
            }
            
            response = requests.post(order_book_url, json=order_book_payload, timeout=10)
            response.raise_for_status()
            hyper_data = response.json()
            
            # 2. Funding rates and open interest
            funding_url = f"{BASE_URL}/info"
            funding_payload = {
                "type": "clearinghouseState",
                "coin": symbol
            }
            
            funding_response = requests.post(funding_url, json=funding_payload, timeout=10)
            funding_data = funding_response.json()
            
            # Extract institutional data
            hyperliquid_data[symbol] = {
                'order_book': hyper_data,
                'funding_rates': funding_data,
                'institutional_metrics': calculate_hyperliquid_metrics(hyper_data, funding_data)
            }
            
        except Exception as e:
            print(f"Warning: Could not fetch Hyperliquid data for {symbol}: {e}")
            # Fallback to CoinGecko data
            hyperliquid_data[symbol] = None
    
    return hyperliquid_data

def calculate_hyperliquid_metrics(order_book_data, funding_data):
    """Calculate institutional metrics from Hyperliquid data"""
    
    metrics = {}
    
    try:
        # 1. Order Flow Analysis (CVD from order book)
        if 'orderBook' in order_book_data:
            bids = order_book_data['orderBook'].get('bids', [])
            asks = order_book_data['orderBook'].get('asks', [])
            
            # Calculate CVD from order book
            total_bids = sum([bid[1] for bid in bids[:10]])  # Top 10 bids
            total_asks = sum([ask[1] for ask in asks[:10]])  # Top 10 asks
            
            cvd_hyper = (total_bids - total_asks) / (total_bids + total_asks) * 100
            metrics['CVD_Hyperliquid'] = {
                'value': cvd_hyper,
                'interpretation': "Hyperliquid order flow - positive = more bids"
            }
        
        # 2. Funding Rates (institutional sentiment)
        if 'fundingRates' in funding_data:
            funding_rate = funding_data['fundingRates'].get('rate', 0)
            metrics['Funding_Rate'] = {
                'value': funding_rate,
                'interpretation': f"Funding rate: {funding_rate:.4f} (positive = longs pay shorts)"
            }
        
        # 3. Open Interest (institutional positioning)
        if 'openInterest' in funding_data:
            oi = funding_data['openInterest']
            metrics['Open_Interest'] = {
                'value': oi,
                'interpretation': f"Open interest: {oi:,.0f} (higher = more institutional interest)"
            }
        
        # 4. Liquidation Data (institutional behavior)
        if 'liquidations' in funding_data:
            liquidations = funding_data['liquidations']
            long_liq = liquidations.get('longs', 0)
            short_liq = liquidations.get('shorts', 0)
            
            metrics['Liquidations'] = {
                'longs': long_liq,
                'shorts': short_liq,
                'interpretation': f"Liquidations: Longs: ${long_liq:,.0f}, Shorts: ${short_liq:,.0f}"
            }
        
    except Exception as e:
        print(f"Warning: Could not calculate Hyperliquid metrics: {e}")
        metrics = {}
    
    return metrics

def integrate_hyperliquid_analysis(coin_data, hyperliquid_data):
    """Integrate Hyperliquid data with CoinGecko data"""
    
    if not hyperliquid_data or coin_data['symbol'].upper() not in hyperliquid_data:
        return "No Hyperliquid data available"
    
    symbol = coin_data['symbol'].upper()
    hyper_data = hyperliquid_data[symbol]
    
    if not hyper_data:
        return "No Hyperliquid data available"
    
    analysis = "\n\n*HYPERLIQUID INSTITUTIONAL DATA:*\n"
    
    # Add Hyperliquid metrics
    if 'institutional_metrics' in hyper_data:
        metrics = hyper_data['institutional_metrics']
        
        if 'CVD_Hyperliquid' in metrics:
            analysis += f"• Hyperliquid CVD: {metrics['CVD_Hyperliquid']['value']:+.2f}% ({metrics['CVD_Hyperliquid']['interpretation']})\n"
        
        if 'Funding_Rate' in metrics:
            analysis += f"• Funding Rate: {metrics['Funding_Rate']['value']:.4f} ({metrics['Funding_Rate']['interpretation']})\n"
        
        if 'Open_Interest' in metrics:
            analysis += f"• Open Interest: {metrics['Open_Interest']['value']:,.0f} ({metrics['Open_Interest']['interpretation']})\n"
        
        if 'Liquidations' in metrics:
            analysis += f"• Liquidations: Longs: ${metrics['Liquidations']['longs']:,.0f}, Shorts: ${metrics['Liquidations']['shorts']:,.0f}\n"
    
    return analysis

# At the end of your fetch_crypto_data() function, ADD this:

# HYPERLIQUID INTEGRATION
hyper_data = fetch_hyperliquid_data(['BTC', 'ETH', 'AVAX', 'ARB', 'DOT'])  # Your coins
hyper_analysis = integrate_hyperliquid_analysis(coin_data, hyper_data)
send_to_telegram(hyper_analysis)



