import os
import json
import requests
from flask import Flask, request, jsonify, render_template, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key

# Load itemData from GitHub at startup
def load_item_data():
    local_file = 'itemData.json'
    github_url = "https://raw.githubusercontent.com/AdityaSharma2403/image/main/itemData.json"

    if os.path.exists(local_file):
        os.remove(local_file)

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

# Load once on startup
ITEM_DATA = load_item_data()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        session['token_type'] = request.form.get('token_type')
        session['token'] = request.form.get('token')
        session['region'] = request.form.get('region')
        return redirect(url_for('search'))
    return render_template('setup.html')

@app.route('/search')
def search():
    if 'token' not in session:
        return redirect(url_for('home'))
    return render_template('search.html')

@app.route('/review')
def review():
    if 'token' not in session or 'selected_items' not in session:
        return redirect(url_for('home'))
    return render_template('review.html')

@app.route('/api/search_items', methods=['POST'])
def search_items():
    query = request.json.get('query', '').lower()
    if not query:
        return jsonify({'error': 'Empty query'}), 400
    
    results = []
    for item in ITEM_DATA:
        # Search in itemID (including partial matches)
        if query in str(item.get('itemID', '')):
            results.append(item)
    
    # If no direct matches, search in descriptions
    if not results:
        for item in ITEM_DATA:
            if (query in item.get('description', '').lower() or 
                query in item.get('description2', '').lower() or 
                query in item.get('icon', '').lower()):
                results.append(item)
    
    return jsonify({'results': results[:200]})  # Increased limit to 200 for better discovery

@app.route('/api/get_item_image/<int:item_id>')
def get_item_image(item_id):
    base_url = "https://raw.githubusercontent.com/I-SHOW-AKIRU200/AKIRU-ICONS/main/ICONS"
    image_url = f"{base_url}/{item_id}.png"
    fallback_url = "https://i.ibb.co/ksqnMfy6/profile-Icon-pjx8nu2l7ola1-1-removebg-preview.png"
    
    try:
        response = requests.head(image_url)
        if response.status_code == 200:
            return jsonify({'image_url': image_url})
        return jsonify({'image_url': fallback_url})
    except Exception as e:
        print(f"Error checking image for {item_id}: {e}")
        return jsonify({'image_url': fallback_url})

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
                }
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
    
    return jsonify({'results': responses})

if __name__ == '__main__':
    app.run(debug=True)
