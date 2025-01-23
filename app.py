import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from PyPDF2 import PdfReader
from io import BytesIO
import logging

logging.basicConfig(level=logging.DEBUG)

# Flask App Setup
app = Flask(__name__)
CORS(app)

# Configure the GenAI API
genai.configure(api_key="YOUR_API_KEY")

# Function to download PDF as in-memory object
def download_pdf(pdf_url):
    response = requests.get(pdf_url)
    if response.status_code == 200:
        return BytesIO(response.content)
    else:
        raise Exception(f"Failed to download PDF. Status code: {response.status_code}")

# Route to extract text from PDF
@app.route('/extract', methods=['POST'])
def extract_text():
    try:
        data = request.get_json()
        pdf_path = data.get('file_path')

        if not pdf_path:
            return jsonify({"error": "'file_path' is required."}), 400

        if pdf_path.startswith("http://") or pdf_path.startswith("https://"):
            pdf_file = download_pdf(pdf_path)
            pdf_reader = PdfReader(pdf_file)
        else:
            pdf_reader = PdfReader(pdf_path)

        raw_text = f'filename-{pdf_path}\n'
        for page in pdf_reader.pages:
            content = page.extract_text()
            if content:
                raw_text += content.replace('\n', '\\n') + '\\n'

        return jsonify({"text": raw_text})

    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return jsonify({"error": str(e)}), 500

# Route to query text with GenAI
@app.route('/pdf-query', methods=['POST'])
def pdf_query():
    try:
        data = request.get_json()
        texts = data.get('texts', [])
        user_query = data.get('query')

        if not texts or not user_query:
            return jsonify({"error": "Both 'texts' and 'query' are required."}), 400

        prompt = f"Use the following information:\n{texts}\nAnswer this query:\n{user_query}"
        response = genai.generate_text(prompt=prompt)

        return jsonify({"answer": response.result})

    except Exception as e:
        logging.error(f"Error querying text: {e}")
        return jsonify({"error": str(e)}), 500

# Export app for Vercel
if __name__ == '__main__':
    app.run(debug=False)
