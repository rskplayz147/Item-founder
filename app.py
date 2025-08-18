from flask import Flask, render_template, request, jsonify, send_file
import json
import requests
import io

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
        if (query in str(item['itemID']) or 
            query in item['icon'].lower() or 
            query in item.get('description', '').lower() or 
            query in item.get('description2', '').lower()):
            
            # Add image URL to the item data
            item_with_image = item.copy()
            item_with_image['image_url'] = f"https://raw.githubusercontent.com/I-SHOW-AKIRU200/AKIRU-ICONS/main/ICONS/{item['itemID']}.png"
            results.append(item_with_image)
    
    return jsonify(results)

@app.route('/api/image/icon', methods=['GET'])
def get_image_by_icon():
    icon_name = request.args.get('icon', '').lower()
    
    if not icon_name:
        return jsonify({'error': 'Icon name is required'}), 400
    
    # Search for the item with the matching icon name
    for item in items:
        if item['icon'].lower() == icon_name:
            item_id = item['itemID']
            image_url = f"https://raw.githubusercontent.com/I-SHOW-AKIRU200/AKIRU-ICONS/main/ICONS/{item_id}.png"
            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    # Return the raw image data
                    return send_file(
                        io.BytesIO(response.content),
                        mimetype='image/png',
                        as_attachment=False
                    )
                else:
                    return jsonify({'error': 'Image not found for the given icon name'}), 404
            except requests.RequestException as e:
                return jsonify({'error': f'Failed to fetch image: {str(e)}'}), 500
    
    return jsonify({'error': 'Icon name not found in item data'}), 404

@app.route('/api/image/id', methods=['GET'])
def get_image_by_id():
    item_id = request.args.get('id', '')
    
    if not item_id:
        return jsonify({'error': 'Item ID is required'}), 400
    
    # Verify if item_id exists in itemData.json
    for item in items:
        if str(item['itemID']) == item_id:
            image_url = f"https://raw.githubusercontent.com/I-SHOW-AKIRU200/AKIRU-ICONS/main/ICONS/{item_id}.png"
            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    # Return the raw image data
                    return send_file(
                        io.BytesIO(response.content),
                        mimetype='image/png',
                        as_attachment=False
                    )
                else:
                    return jsonify({'error': 'Image not found for the given item ID'}), 404
            except requests.RequestException as e:
                return jsonify({'error': f'Failed to fetch image: {str(e)}'}), 500
    
    return jsonify({'error': 'Item ID not found in item data'}), 404

if __name__ == '__main__':
    app.run(debug=True)
