import os
import json
import requests
from datetime import timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# Load item data
def load_item_data():
    try:
        response = requests.get("https://raw.githubusercontent.com/AdityaSharma2403/image/main/itemData.json")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error loading item data: {e}")
        return []

ITEM_DATA = load_item_data()

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

# API Endpoints
@app.route('/api/search_items', methods=['POST'])
def search_items():
    query = request.json.get('query', '').lower()
    results = [item for item in ITEM_DATA 
              if query in str(item.get('itemID', '')) or
              query in item.get('description', '').lower() or
              query in item.get('description2', '').lower()]
    return jsonify({'results': results[:200]})

@app.route('/api/get_item_image/<int:item_id>')
def get_item_image(item_id):
    image_url = f"https://raw.githubusercontent.com/I-SHOW-AKIRU200/AKIRU-ICONS/main/ICONS/{item_id}.png"
    try:
        if requests.head(image_url, timeout=3).status_code == 200:
            return jsonify({'image_url': image_url})
    except:
        pass
    return jsonify({'image_url': "https://i.ibb.co/ksqnMfy6/profile-Icon-pjx8nu2l7ola1-1-removebg-preview.png"})

@app.route('/api/prepare_review', methods=['POST'])
def prepare_review():
    if not (data := request.get_json()) or not (items := data.get('items')):
        return jsonify({'error': 'No items selected'}), 400
    session['selected_items'] = items
    return jsonify({'redirect_url': url_for('review')})

@app.route('/api/add_selected', methods=['POST'])
def add_selected():
    items = request.json.get('items', [])
    responses = []
    for item_id in items:
        try:
            response = requests.get(
                'https://akiru-wishlist.vercel.app/' + 
                ('access_add' if session.get('token_type') == 'access' else 'jwt_add'),
                params={
                    'item_id': item_id,
                    session.get('token_type', 'access') + '_token': session.get('token'),
                    'region': session.get('region', 'na')
                },
                timeout=5
            )
            responses.append({
                'item_id': item_id,
                'status': response.status_code,
                'response': response.json()
            })
        except Exception as e:
            responses.append({'item_id': item_id, 'status': 500, 'error': str(e)})
    
    if all(r['status'] == 200 for r in responses):
        session.pop('selected_items', None)
    return jsonify({'results': responses})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
