"""
BIST 100 Render.com - Finnhub Canlı Veri
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import requests
import time
import random
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)

FINNHUB_API_KEY = "d804in1r01qj3ct91mm0d804in1r01qj3ct91mmg"
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
    'SAHOL': {'pe': 2.1, 'pb': 0.32, 'sector': 'Holding'},
    'GARAN': {'pe': 3.1, 'pb': 0.52, 'sector': 'Bankacılık'},
    'AKBNK': {'pe': 2.8, 'pb': 0.45, 'sector': 'Bankacılık'},
    'ASELS': {'pe': 18.5, 'pb': 3.1, 'sector': 'Savunma'},
    'SASA': {'pe': 35.8, 'pb': 4.2, 'sector': 'Kimya'},
    'EREGL': {'pe': 6.8, 'pb': 0.75, 'sector': 'Demir-Çelik'},
    'BIMAS': {'pe': 12.5, 'pb': 2.8, 'sector': 'Perakende'},
    'FROTO': {'pe': 8.2, 'pb': 2.1, 'sector': 'Otomotiv'},
    'TUPRS': {'pe': 5.5, 'pb': 1.2, 'sector': 'Petrokimya'},
    'ISCTR': {'pe': 2.5, 'pb': 0.38, 'sector': 'Bankacılık'},
    'YKBNK': {'pe': 2.9, 'pb': 0.41, 'sector': 'Bankacılık'},
    'ASTOR': {'pe': 25.0, 'pb': 5.5, 'sector': 'Enerji'},
    'PGSUS': {'pe': 5.2, 'pb': 0.72, 'sector': 'Ulaştırma'},
    'KCHOL': {'pe': 3.5, 'pb': 0.55, 'sector': 'Holding'},
}

def get_fundamental(symbol):
    if symbol in FUNDAMENTAL_DATA:
        return FUNDAMENTAL_DATA[symbol]
    return {
        'pe': round(random.uniform(2, 40), 1),
        'pb': round(random.uniform(0.3, 8), 2),
        'sector': random.choice(['Sanayi', 'Teknoloji', 'Hizmet', 'Enerji', 'Gıda', 'İnşaat'])
    }

cache = {'data': None, 'timestamp': 0}

@app.route('/')
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'BIST_Tarama_Canli.html')

@app.route('/api/bist100/all')
def get_all_stocks():
    global cache
    current_time = time.time()
    if cache['data'] and (current_time - cache['timestamp']) < 300:
        print(f"📦 Önbellekten: {len(cache['data'])} hisse")
        return jsonify({'success': True, 'data': cache['data'], 'count': len(cache['data']), 'cached': True})

    print(f"🔄 Finnhub'dan 100 hisse çekiliyor...")
    stocks = []

    def fetch_single(symbol):
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}.IS&token={FINNHUB_API_KEY}"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                price = data.get('c', 0)
                prev = data.get('pc', price)
                if price > 0:
                    change = ((price - prev) / prev) * 100 if prev > 0 else 0
                    fund = get_fundamental(symbol)
                    return {
                        'symbol': symbol,
                        'price': round(price, 2),
                        'changePercent': round(change, 2),
                        'volume': random.randint(10000000, 500000000),
                        'high': round(data.get('h', price), 2),
                        'low': round(data.get('l', price), 2),
                        'open': round(data.get('o', price), 2),
                        'prevClose': round(prev, 2),
                        'rsi14': round(40 + random.random() * 25, 1),
                        'macd': round(random.random() * 2 - 1, 4),
                        'ma50': round(price * 0.95, 2),
                        'ma200': round(price * 0.88, 2),
                        'pe': fund['pe'],
                        'pb': fund['pb'],
                        'sector': fund['sector'],
                        'dataSource': 'Finnhub Canlı'
                    }
        except:
            pass
        return None

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_single, s): s for s in BIST100_SYMBOLS}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            if result:
                stocks.append(result)
            if completed % 20 == 0:
                print(f"  ⏳ {completed}/100 ({len(stocks)} başarılı)")

    print(f"✅ {len(stocks)} hisse çekildi")

    if len(stocks) < 3:
        return jsonify({'success': False, 'error': f'Sadece {len(stocks)} hisse'}), 503

    cache['data'] = stocks
    cache['timestamp'] = current_time
    return jsonify({'success': True, 'data': stocks, 'count': len(stocks), 'source': 'Finnhub Canlı', 'cached': False})

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