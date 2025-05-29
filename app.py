from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

# Load item data
with open('itemData.json', 'r') as f:
    items = json.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['GET'])
def search_items():
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify([])
    
    results = []
    for item in items:
        # Search in itemID, icon, description, description2
        if (query in str(item['itemID']) or \
           (query in item['icon'].lower()) or \
           (query in item.get('description', '').lower()) or \
           (query in item.get('description2', '').lower()):
            
            # Add image URL to the item data
            item_with_image = item.copy()
            item_with_image['image_url'] = f"https://raw.githubusercontent.com/I-SHOW-AKIRU200/AKIRU-ICONS/main/ICONS/{item['itemID']}.png"
            results.append(item_with_image)
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
