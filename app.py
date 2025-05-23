import os
import json
import requests
from datetime import timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# Load itemData from GitHub
def load_item_data():
    local_file = 'itemData.json'
    github_url = "https://raw.githubusercontent.com/AdityaSharma2403/image/main/itemData.json"

    if os.path.exists(local_file):
        with open(local_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    try:
        response = requests.get(github_url)
        response.raise_for_status()
        data = response.json()

        with open(local_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        return data
    except Exception as e:
        print("Error loading itemData:", e)
        return []

ITEM_DATA = load_item_data()

@app.route('/')
def home():
    if 'token' in session:
        return redirect(url_for('search'))
    return render_template('home.html')

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        session.permanent = True
        session['token_type'] = request.form.get('token_type')
        session['token'] = request.form.get('token')
        session['region'] = request.form.get('region')
        return redirect(url_for('search'))
    
    if 'token' in session:
        return redirect(url_for('search'))
    
    return render_template('setup.html')

@app.route('/search')
def search():
    if 'token' not in session:
        return redirect(url_for('setup'))
    return render_template('search.html')

@app.route('/review')
def review():
    if 'token' not in session:
        return redirect(url_for('setup'))
    if 'selected_items' not in session or not session['selected_items']:
        return redirect(url_for('search'))
    return render_template('review.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/api/search_items', methods=['POST'])
def search_items():
    if 'token' not in session:
        return jsonify({'error': 'Session expired'}), 401
    
    query = request.json.get('query', '').lower()
    if not query:
        return jsonify({'error': 'Empty query'}), 400
    
    results = []
    for item in ITEM_DATA:
        if query in str(item.get('itemID', '')):
            results.append(item)
    
    if not results:
        for item in ITEM_DATA:
            if (query in item.get('description', '').lower() or 
                query in item.get('description2', '').lower()):
                results.append(item)
    
    return jsonify({'results': results[:200]})

@app.route('/api/get_item_image/<int:item_id>')
def get_item_image(item_id):
    base_url = "https://raw.githubusercontent.com/I-SHOW-AKIRU200/AKIRU-ICONS/main/ICONS"
    image_url = f"{base_url}/{item_id}.png"
    fallback_url = "https://i.ibb.co/ksqnMfy6/profile-Icon-pjx8nu2l7ola1-1-removebg-preview.png"
    
    try:
        response = requests.head(image_url, timeout=3)
        if response.status_code == 200:
            return jsonify({'image_url': image_url})
        return jsonify({'image_url': fallback_url})
    except Exception:
        return jsonify({'image_url': fallback_url})

@app.route('/api/prepare_review', methods=['POST'])
def prepare_review():
    if 'token' not in session:
        return jsonify({'error': 'Session expired'}), 401
    
    data = request.get_json()
    selected_items = data.get('items', [])
    
    if not selected_items:
        return jsonify({'error': 'No items selected'}), 400
    
    session['selected_items'] = selected_items
    return jsonify({'redirect_url': url_for('review')})

@app.route('/api/add_selected', methods=['POST'])
def add_selected():
    if 'token' not in session:
        return jsonify({'error': 'Session expired'}), 401
    
    selected_items = request.json.get('items', [])
    if not selected_items:
        return jsonify({'error': 'No items selected'}), 400
    
    token_type = session.get('token_type', 'access')
    token = session.get('token', '')
    region = session.get('region', 'na')
    
    endpoint = 'https://akiru-wishlist.vercel.app/access_add' if token_type == 'access' else 'https://akiru-wishlist.vercel.app/jwt_add'
    param_name = 'access_token' if token_type == 'access' else 'jwt_token'
    
    responses = []
    for item_id in selected_items:
        try:
            response = requests.get(
                endpoint,
                params={
                    'item_id': item_id,
                    param_name: token,
                    'region': region
                },
                timeout=5
            )
            responses.append({
                'item_id': item_id,
                'status': response.status_code,
                'response': response.json()
            })
        except Exception as e:
            responses.append({
                'item_id': item_id,
                'status': 500,
                'error': str(e)
            })
    
    if all(res['status'] == 200 for res in responses):
        session.pop('selected_items', None)
    
    return jsonify({'results': responses})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
