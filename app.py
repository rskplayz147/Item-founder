from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load item data
try:
    with open('itemData.json', 'r') as f:
        items = json.load(f)
except FileNotFoundError:
    items = []
    print("Warning: itemData.json not found. Using empty list.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['GET'])
def search_items():
    query = request.args.get('q', '').lower().strip()
    
    if not query:
        return jsonify([])
    
    results = []
    for item in items:
        try:
            # Search across multiple fields
            if (query in str(item.get('itemID', '')) or \
                query in item.get('icon', '').lower() or \
                query in item.get('description', '').lower() or \
                query in item.get('description2', '').lower()):
                
                # Add image URL to the item data
                item_with_image = item.copy()
                item_with_image['image_url'] = f"https://raw.githubusercontent.com/I-SHOW-AKIRU200/AKIRU-ICONS/main/ICONS/{item.get('itemID', '')}.png"
                results.append(item_with_image)
        except Exception as e:
            print(f"Error processing item {item.get('itemID')}: {str(e)}")
            continue
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
