import os
import json
import requests
from datetime import timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secure-key-123')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# Constants
WISHLIST_API = "https://akiru-wishlist.vercel.app/"
ITEM_DATA_URL = "https://raw.githubusercontent.com/AdityaSharma2403/image/main/itemData.json"
IMAGE_BASE_URL = "https://raw.githubusercontent.com/I-SHOW-AKIRU200/AKIRU-ICONS/main/ICONS/"
FALLBACK_IMAGE = "https://i.ibb.co/ksqnMfy6/profile-Icon-pjx8nu2l7ola1-1-removebg-preview.png"

# Load and cache item data
def load_item_data():
    try:
        response = requests.get(ITEM_DATA_URL, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error loading item data: {e}")
        return []

ITEM_DATA = load_item_data()

# Helper function for wishlist operations
def wishlist_operation(item_ids, operation):
    token_type = session.get('token_type')
    token = session.get('token')
    region = session.get('region', 'na')
    
    endpoint = f"{token_type}_{operation}"
    param_name = f"{token_type}_token"
    
    results = []
    for item_id in item_ids:
        try:
            response = requests.get(
                f"{WISHLIST_API}{endpoint}",
                params={
                    'item_id': item_id,
                    param_name: token,
                    'region': region
                },
                timeout=5
            )
            results.append({
                'item_id': item_id,
                'status': response.status_code,
                'response': response.json()
            })
        except Exception as e:
            results.append({
                'item_id': item_id,
                'status': 500,
                'error': str(e)
            })
    return results

# Routes
@app.route('/')
def home():
    if 'token' in session:
        return redirect(url_for('search'))
    return render_template('home.html')

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        session.permanent = True
        session.update({
            'token_type': request.form.get('token_type'),
            'token': request.form.get('token'),
            'region': request.form.get('region', 'na')
        })
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
    if 'token' not in session or not session.get('selected_items'):
        return redirect(url_for('search'))
    return render_template('review.html')

# API Endpoints
@app.route('/api/search', methods=['POST'])
def api_search():
    query = request.json.get('query', '').lower()
    results = [
        item for item in ITEM_DATA
        if (query in str(item.get('itemID', ''))) or
           (query in item.get('description', '').lower()) or
           (query in item.get('description2', '').lower())
    ][:200]  # Limit to 200 results
    return jsonify(results)

@app.route('/api/check_image/<int:item_id>')
def check_image(item_id):
    image_url = f"{IMAGE_BASE_URL}{item_id}.png"
    try:
        if requests.head(image_url, timeout=3).status_code == 200:
            return jsonify({'url': image_url})
    except:
        pass
    return jsonify({'url': FALLBACK_IMAGE})

@app.route('/api/save_selection', methods=['POST'])
def save_selection():
    if 'token' not in session:
        return jsonify({'error': 'Session expired'}), 401
        
    items = request.json.get('items', [])
    if not items:
        return jsonify({'error': 'No items selected'}), 400
        
    session['selected_items'] = items
    return jsonify({'redirect_url': url_for('review')})

@app.route('/api/add_items', methods=['POST'])
def add_items():
    if 'token' not in session:
        return jsonify({'error': 'Session expired'}), 401
        
    items = request.json.get('items', [])
    if not items:
        return jsonify({'error': 'No items selected'}), 400
        
    results = wishlist_operation(items, 'add')
    
    if all(r['status'] == 200 for r in results):
        session.pop('selected_items', None)
        
    return jsonify({'results': results})

@app.route('/api/remove_items', methods=['POST'])
def remove_items():
    if 'token' not in session:
        return jsonify({'error': 'Session expired'}), 401
        
    items = request.json.get('items', [])
    if not items:
        return jsonify({'error': 'No items selected'}), 400
        
    results = wishlist_operation(items, 'delete')
    return jsonify({'results': results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
