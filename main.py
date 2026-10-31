import json, os, time, ccxt, pandas as pd
from datetime import datetime

with open('config.json') as f:
    cfg = json.load(f)

api_key = os.getenv('API_KEY', cfg['api_key'])
secret_key = os.getenv('SECRET_KEY', cfg['secret_key'])

bybit = ccxt.bybit({
    'apiKey': api_key,
    'secret': secret_key,
    'enableRateLimit': True,
})

if cfg['mode'] == 'paper':
    bybit.set_sandbox_mode(True)

log_file = cfg['log_file']
pd.DataFrame(columns=['time', 'pair', 'signal', 'pnl', 'dd']).to_csv(log_file, index=False)

def run_cycle():
    now = datetime.utcnow().isoformat()
    print(f"[{now}] Запуск цикла...")
    
    for pair in cfg['pairs']:
        try:
            ohlcv = bybit.fetch_ohlcv(pair, timeframe='1h', limit=50)
            df = pd.DataFrame(ohlcv, columns=['time','open','high','low','close','volume'])
            
            close = df['close'].iloc[-1]
            high_24h = df['high'].max()
            low_24h = df['low'].min()
            
            signal = 'HOLD'
            if close > high_24h * 0.98: signal = 'TREND_LONG'
            elif close < low_24h * 1.02: signal = 'TREND_SHORT'
            
            virtual_pnl = round((close - df['open'].iloc[-1]) / df['open'].iloc[-1] * cfg['risk_per_trade_pct'], 4)
            
            print(f"[{pair}] Signal: {signal} | Virtual PnL: {virtual_pnl}%")
            
            pd.DataFrame([[now, pair, signal, virtual_pnl, 0]], columns=['time','pair','signal','pnl','dd']).to_csv(log_file, mode='a', header=False, index=False)
        except Exception as e:
            print(f"[{pair}] Ошибка: {e}")

run_cycle()
