from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

# Load item data
with open('itemData.json', 'r') as f:
    items = json.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    results = []
    for item in items:
        if (query in str(item['itemID']) or 
            query in item['icon'].lower() or 
            query in item['description'].lower() or 
            (item['description2'] and query in item['description2'].lower())):
            results.append(item)
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
