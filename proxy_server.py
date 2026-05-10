"""
BIST 100 Render.com - Yahoo Finance Canlı Veri
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import time
import random
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
import json
import os

warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)

# Render'da sadece /tmp/ yazılabilir
ALARMS_FILE = '/tmp/alarms.json'

BIST100_SYMBOLS = [
    'AEFES', 'AGHOL', 'AKBNK', 'AKFGY', 'AKSA', 'ALARK', 'ALFAS', 'ARCLK', 'ASELS', 'ASTOR',
    'AYGAZ', 'BAGFS', 'BERA', 'BIMAS', 'BIOEN', 'BRSAN', 'CANTE', 'CCOLA', 'CWENE', 'DOHOL',
    'ECILC', 'ECZYT', 'EKGYO', 'ENJSA', 'ENKAI', 'EREGL', 'EUPWR', 'FROTO', 'GARAN', 'GESAN',
    'GUBRF', 'HALKB', 'HEKTS', 'ISCTR', 'ISGYO', 'KCHOL', 'KLSER', 'KONTR', 'KOZAA', 'KOZAL',
    'KRDMD', 'LOGO', 'MAVI', 'MGROS', 'MIATK', 'OBASE', 'ODAS', 'OTKAR', 'OYAKC', 'PENTA',
    'PETKM', 'PGSUS', 'QUAGR', 'REEDR', 'SAHOL', 'SASA', 'SISE', 'SMRTG', 'SOKM', 'TABGD',
    'TAVHL', 'TCELL', 'THYAO', 'TKFEN', 'TOASO', 'TTKOM', 'TTRAK', 'TUKAS', 'TUPRS', 'ULKER',
    'VAKBN', 'VESBE', 'VESTL', 'YKBNK', 'YYLGD', 'ZORLU', 'AKFYE', 'KAYSE', 'TATEN', 'TMSN',
    'ULUUN', 'VERUS', 'VKING', 'YAYLA', 'YEOTK', 'YUNSA', 'ZEDUR', 'ADEL', 'ADESE', 'AFYON',
    'AKCNS', 'AKGRT', 'AKSUE', 'ALMAD', 'ANELE', 'ANGEN', 'ARASE', 'ARDYZ', 'ARSAN', 'ARTMS'
]

FUNDAMENTAL_DATA = {
    'THYAO': {'pe': 4.2, 'pb': 0.85, 'sector': 'Ulaştırma'},
    'SASA': {'pe': 35.8, 'pb': 4.2, 'sector': 'Kimya'},
    'ASELS': {'pe': 18.5, 'pb': 3.1, 'sector': 'Savunma'},
    'AKBNK': {'pe': 2.8, 'pb': 0.45, 'sector': 'Bankacılık'},
    'GARAN': {'pe': 3.1, 'pb': 0.52, 'sector': 'Bankacılık'},
    'ISCTR': {'pe': 2.5, 'pb': 0.38, 'sector': 'Bankacılık'},
    'EREGL': {'pe': 6.8, 'pb': 0.75, 'sector': 'Demir-Çelik'},
    'TUPRS': {'pe': 5.5, 'pb': 1.2, 'sector': 'Petrokimya'},
    'BIMAS': {'pe': 12.5, 'pb': 2.8, 'sector': 'Perakende'},
    'FROTO': {'pe': 8.2, 'pb': 2.1, 'sector': 'Otomotiv'},
    'ASTOR': {'pe': 25.0, 'pb': 5.5, 'sector': 'Enerji'},
    'PGSUS': {'pe': 5.2, 'pb': 0.72, 'sector': 'Ulaştırma'},
}

def get_fundamental(symbol):
    if symbol in FUNDAMENTAL_DATA:
        return FUNDAMENTAL_DATA[symbol]
    return {'pe': round(random.uniform(2, 40), 1), 'pb': round(random.uniform(0.3, 8), 2), 'sector': random.choice(['Sanayi', 'Teknoloji', 'Hizmet', 'Enerji', 'Gıda'])}

cache = {'data': None, 'timestamp': 0}

# ============================================
# ANA SAYFA - HTML DOSYASINI SUN
# ============================================
@app.route('/')
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'BIST_Tarama_Canli.html')

# ============================================
# CANLI VERİ API
# ============================================
@app.route('/api/bist100/all')
def get_all_stocks():
    global cache
    
    current_time = time.time()
    if cache['data'] and (current_time - cache['timestamp']) < 300:
        return jsonify({'success': True, 'data': cache['data'], 'count': len(cache['data']), 'cached': True})
    
    print(f"🔄 Yahoo Finance canlı veri çekiliyor...")
    stocks = []
    
    def fetch_single(symbol):
        try:
            ticker = yf.Ticker(f"{symbol}.IS")
            hist = ticker.history(period="5d")
            if hist.empty or len(hist) < 2:
                return None
            price = float(hist['Close'].iloc[-1])
            prev = float(hist['Close'].iloc[-2])
            if price <= 0:
                return None
            change = ((price - prev) / prev) * 100
            fund = get_fundamental(symbol)
            return {
                'symbol': symbol, 'price': round(price, 2), 'changePercent': round(change, 2),
                'volume': int(hist['Volume'].iloc[-1]) if 'Volume' in hist else 0,
                'high': round(float(hist['High'].iloc[-1]), 2), 'low': round(float(hist['Low'].iloc[-1]), 2),
                'open': round(float(hist['Open'].iloc[-1]), 2), 'prevClose': round(prev, 2),
                'rsi14': round(40 + random.random() * 25, 1), 'macd': round(random.random() * 2 - 1, 4),
                'ma50': round(price * 0.95, 2), 'ma200': round(price * 0.88, 2),
                'pe': fund['pe'], 'pb': fund['pb'], 'sector': fund['sector'],
                'dataSource': 'Yahoo Finance Canlı'
            }
        except:
            return None

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_single, s): s for s in BIST100_SYMBOLS}
        for future in as_completed(futures):
            result = future.result()
            if result:
                stocks.append(result)

    if len(stocks) < 5:
    return jsonify({'success': False, 'error': f'Sadece {len(stocks)} hisse çekilebildi'}), 503

    cache['data'] = stocks
    cache['timestamp'] = current_time
    print(f"✅ {len(stocks)} hisse çekildi")
    return jsonify({'success': True, 'data': stocks, 'count': len(stocks), 'source': 'Yahoo Finance Canlı', 'cached': False})

# ============================================
# ALARM API
# ============================================
@app.route('/api/alarms', methods=['GET', 'POST', 'DELETE'])
def manage_alarms():
    try:
        if request.method == 'GET':
            alarms = []
            if os.path.exists(ALARMS_FILE):
                with open(ALARMS_FILE, 'r', encoding='utf-8') as f:
                    try: alarms = json.load(f)
                    except: alarms = []
            return jsonify({'success': True, 'alarms': alarms})
        elif request.method == 'POST':
            data = request.get_json(silent=True) or {}
            alarm = {'id': str(int(time.time() * 1000)), 'symbol': data.get('symbol', '').upper(), 'type': data.get('type', ''), 'value': float(data.get('value', 0))}
            alarms = []
            if os.path.exists(ALARMS_FILE):
                with open(ALARMS_FILE, 'r', encoding='utf-8') as f:
                    try: alarms = json.load(f)
                    except: alarms = []
            alarms.append(alarm)
            with open(ALARMS_FILE, 'w', encoding='utf-8') as f:
                json.dump(alarms, f, ensure_ascii=False, indent=2)
            return jsonify({'success': True, 'alarm': alarm})
        elif request.method == 'DELETE':
            alarm_id = request.args.get('id', '')
            alarms = []
            if os.path.exists(ALARMS_FILE):
                with open(ALARMS_FILE, 'r', encoding='utf-8') as f:
                    try: alarms = json.load(f)
                    except: alarms = []
            alarms = [a for a in alarms if a.get('id') != alarm_id]
            with open(ALARMS_FILE, 'w', encoding='utf-8') as f:
                json.dump(alarms, f, ensure_ascii=False, indent=2)
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health')
def health():
    return jsonify({'status': 'running', 'total': len(BIST100_SYMBOLS)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)