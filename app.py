import os
import requests
from flask import Flask, render_template, redirect, url_for, session, jsonify
from datetime import timedelta

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# API Config
API_BASE = "https://akiru-wishlist.vercel.app/"
ITEM_DATA_URL = "https://raw.githubusercontent.com/AdityaSharma2403/image/main/itemData.json"
ICON_BASE = "https://raw.githubusercontent.com/I-SHOW-AKIRU200/AKIRU-ICONS/main/ICONS/"
FALLBACK_IMG = "https://i.ibb.co/ksqnMfy6/profile-Icon-pjx8nu2l7ola1-1-removebg-preview.png"

def get_item_data():
    try:
        return requests.get(ITEM_DATA_URL).json()
    except:
        return []

ITEMS = get_item_data()

@app.route('/')
def home():
    if 'token' in session:
        return redirect(url_for('search'))
    return render_template('index.html')

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        session.update({
            'token_type': request.form['token_type'],
            'token': request.form['token'],
            'region': request.form['region']
        })
        return redirect(url_for('search'))
    return render_template('setup.html')

@app.route('/search')
def search():
    if 'token' not in session:
        return redirect(url_for('setup'))
    return render_template('search.html')

@app.route('/review')
def review():
    if not session.get('selected_items'):
        return redirect(url_for('search'))
    return render_template('review.html')

@app.route('/api/items', methods=['POST'])
def api_items():
    query = request.json.get('q', '').lower()
    results = [item for item in ITEMS if (
        query in str(item['itemID']) or
        query in item.get('description', '').lower() or
        query in item.get('description2', '').lower()
    )][:100]
    return jsonify(results)

@app.route('/api/wishlist', methods=['POST'])
def api_wishlist():
    action = request.json.get('action')
    items = request.json.get('items', [])
    
    responses = []
    for item_id in items:
        try:
            resp = requests.get(
                f"{API_BASE}{session['token_type']}_{action}",
                params={
                    'item_id': item_id,
                    f"{session['token_type']}_token": session['token'],
                    'region': session.get('region', 'na')
                },
                timeout=5
            )
            responses.append({
                'id': item_id,
                'status': resp.status_code,
                'data': resp.json()
            })
        except Exception as e:
            responses.append({
                'id': item_id,
                'status': 500,
                'error': str(e)
            })
    
    if action == 'add' and all(r['status'] == 200 for r in responses):
        session.pop('selected_items', None)
    
    return jsonify(responses)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
