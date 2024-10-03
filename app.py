import os
import base64
import requests
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")


VISION_API_URL = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"

TRANSLATE_API_URL = f"https://translation.googleapis.com/language/translate/v2?key={API_KEY}"

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('upload.html')

# Route to upload image and process it
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    # Check if file has a valid name and extension
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        image_content = file.read()

        image_base64 = base64.b64encode(image_content).decode('utf-8')

        vision_payload = {
            "requests": [{
                "image": {
                    "content": image_base64
                },
                "features": [{
                    "type": "LABEL_DETECTION",
                    "maxResults": 5
                }]
            }]
        }

        # Make request to Vision API
        vision_response = requests.post(VISION_API_URL, json=vision_payload)
        vision_data = vision_response.json()

        if 'error' in vision_data:
            return jsonify({"error": vision_data['error']['message']}), 400

        # Get detected object labels
        labels = [annotation['description'] for annotation in vision_data['responses'][0].get('labelAnnotations', [])]

        # Translate detected labels to a specified language
        target_language = request.form.get('language', 'es')  # Default is Spanish (es)
        translate_payload = {
            "q": labels,
            "target": target_language
        }

        # Make request to Translate API
        translate_response = requests.post(TRANSLATE_API_URL, json=translate_payload)
        translate_data = translate_response.json()

        # Check for Translate API errors
        if 'error' in translate_data:
            return jsonify({"error": translate_data['error']['message']}), 400

        # Extract translations
        translations = [translation['translatedText'] for translation in translate_data['data']['translations']]

        return jsonify({
            "original_labels": labels,
            "translated_labels": translations
        })

    return jsonify({"error": "Invalid file type"}), 400


if __name__ == '__main__':
    app.run(debug=True)
