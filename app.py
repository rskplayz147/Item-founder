from flask import Flask, render_template, request, jsonify, send_file
import json
import requests
import io
import os

app = Flask(__name__)

# Safe JSON loader
def load_json_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

# Load item data
items = load_json_file("itemData.json")
fallback_items = load_json_file("items-OB50-live.json")

# Helper function to fetch image
def fetch_image(item_id):
    image_url = f"https://raw.githubusercontent.com/I-SHOW-AKIRU200/AKIRU-ICONS/main/ICONS/{item_id}.png"
    try:
        response = requests.get(image_url, timeout=5)
        if response.status_code == 200:
            return send_file(
                io.BytesIO(response.content),
                mimetype="image/png",
                download_name=f"{item_id}.png"
            )
        else:
            return None
    except requests.RequestException:
        return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/search", methods=["GET"])
def search_items():
    query = request.args.get("q", "").lower()
    if not query:
        return jsonify([])

    results = []
    for item in items:
        if (
            query in str(item.get("itemID", "")) or
            query in item.get("icon", "").lower() or
            query in item.get("description", "").lower() or
            query in item.get("description2", "").lower()
        ):
            item_with_image = item.copy()
            item_with_image["image_url"] = f"https://raw.githubusercontent.com/I-SHOW-AKIRU200/AKIRU-ICONS/main/ICONS/{item.get('itemID')}.png"
            results.append(item_with_image)

    return jsonify(results)

@app.route("/api/image/icon", methods=["GET"])
def get_image_by_icon():
    icon_name = request.args.get("icon", "").lower()
    if not icon_name:
        return jsonify({"error": "Icon name is required"}), 400

    for item in items:
        if item.get("icon", "").lower() == icon_name:
            result = fetch_image(item.get("itemID"))
            return result if result else (jsonify({"error": "Image not found"}), 404)

    return jsonify({"error": "Icon name not found in item data"}), 404

@app.route("/api/image/id", methods=["GET"])
def get_image_by_id():
    item_id = request.args.get("id", "")
    if not item_id:
        return jsonify({"error": "Item ID is required"}), 400

    # Check in main items
    for item in items:
        if str(item.get("itemID")) == item_id:
            result = fetch_image(item_id)
            return result if result else (jsonify({"error": "Image not found"}), 404)

    # Check in fallback items
    for item in fallback_items:
        if str(item.get("itemID")) == item_id:
            result = fetch_image(item_id)
            return result if result else (jsonify({"error": "Image not found in fallback data"}), 404)

    return jsonify({"error": "Item ID not found in item data"}), 404

if __name__ == "__main__":
    app.run(debug=True)
