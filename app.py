from flask import Flask, render_template, request, jsonify, send_file
import json
import requests
import io
import os
from typing import List, Dict, Optional
from werkzeug.exceptions import BadRequest, NotFound

app = Flask(__name__)

# Constants
ITEMS_FILE = "itemData.json"
FALLBACK_ITEMS_FILE = "items-OB50-live.json"
IMAGE_URL_TEMPLATE = "https://raw.githubusercontent.com/I-SHOW-AKIRU200/AKIRU-ICONS/main/ICONS/{}.png"
REQUEST_TIMEOUT = 5

# Safe JSON loader
def load_json_file(path: str) -> List[Dict]:
    """
    Load JSON file safely and return a list of dictionaries.
    Returns empty list if file doesn't exist or is invalid.
    """
    try:
        if not os.path.exists(path):
            app.logger.warning(f"File not found: {path}")
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                app.logger.error(f"Invalid JSON format in {path}: Expected a list")
                return []
            return data
    except (json.JSONDecodeError, IOError) as e:
        app.logger.error(f"Error loading JSON file {path}: {str(e)}")
        return []

# Load item data at startup
items: List[Dict] = load_json_file(ITEMS_FILE)
fallback_items: List[Dict] = load_json_file(FALLBACK_ITEMS_FILE)

# Helper function to fetch image
def fetch_image(item_id: str) -> Optional[send_file]:
    """
    Fetch image from remote URL and return it as a file response.
    Returns None if the image cannot be retrieved.
    """
    if not item_id:
        app.logger.warning("Empty item_id provided for image fetch")
        return None

    image_url = IMAGE_URL_TEMPLATE.format(item_id)
    try:
        response = requests.get(image_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()  # Raise exception for bad status codes
        return send_file(
            io.BytesIO(response.content),
            mimetype="image/png",
            as_attachment=False,
            download_name=f"{item_id}.png"
        )
    except requests.RequestException as e:
        app.logger.error(f"Error fetching image for item {item_id}: {str(e)}")
        return None

@app.route("/")
def index():
    """Render the main index page."""
    return render_template("index.html")

@app.route("/api/search", methods=["GET"])
def search_items():
    """
    Search items by query string in itemID, icon, description, or description2.
    Returns a JSON list of matching items with image URLs.
    """
    query = request.args.get("q", "").lower().strip()
    if not query:
        return jsonify([]), 200

    results = []
    for item in items:
        if any(
            query in str(item.get(key, "")).lower()
            for key in ("itemID", "icon", "description", "description2")
        ):
            item_with_image = item.copy()
            item_with_image["image_url"] = IMAGE_URL_TEMPLATE.format(item.get("itemID", ""))
            results.append(item_with_image)

    return jsonify(results), 200

@app.route("/api/image/icon", methods=["GET"])
def get_image_by_icon():
    """
    Fetch and display image by icon name.
    Returns the image file or an error message.
    """
    icon_name = request.args.get("icon", "").lower().strip()
    if not icon_name:
        raise BadRequest("Icon name is required")

    for item in items:
        if item.get("icon", "").lower() == icon_name:
            item_id = item.get("itemID")
            if not item_id:
                raise NotFound("Item ID not found for the given icon")
            result = fetch_image(item_id)
            if result:
                return result
            raise NotFound(f"Image not found for icon: {icon_name}")

    raise NotFound(f"Icon name not found in item data: {icon_name}")

@app.route("/api/image/id", methods=["GET"])
def get_image_by_id():
    """
    Fetch and display image by item ID from main or fallback items.
    Returns the image file or an error message.
    """
    item_id = request.args.get("id", "").strip()
    if not item_id:
        raise BadRequest("Item ID is required")

    # Check in main items
    for item in items:
        if str(item.get("itemID", "")) == item_id:
            result = fetch_image(item_id)
            if result:
                return result
            raise NotFound(f"Image not found for item ID: {item_id}")

    # Check in fallback items
    for item in fallback_items:
        if str(item.get("itemID", "")) == item_id:
            result = fetch_image(item_id)
            if result:
                return result
            raise NotFound(f"Image not found for item ID in fallback data: {item_id}")

    raise NotFound(f"Item ID not found in item data: {item_id}")

# Global error handling
@app.errorhandler(BadRequest)
def handle_bad_request(e):
    """Handle 400 Bad Request errors."""
    return jsonify({"error": str(e)}), 400

@app.errorhandler(NotFound)
def handle_not_found(e):
    """Handle 404 Not Found errors."""
    return jsonify({"error": str(e)}), 404

@app.errorhandler(Exception)
def handle_general_exception(e):
    """Handle unexpected errors."""
    app.logger.error(f"Unexpected error: {str(e)}")
    return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
