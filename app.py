import os
import json
import base64
import requests
from flask import Flask, request, render_template_string, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- HTML TEMPLATE (Embedded for a single-file app) ---
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            background-color: #f3f4f6;
        }
        .container {
            max-width: 800px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .spinner {
            border: 4px solid rgba(0, 0, 0, 0.1);
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border-left-color: #1a73e8;
            animation: spin 1s ease infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body class="bg-gray-100 p-8">
    <div class="container mx-auto bg-white rounded-xl shadow-lg p-8 sm:p-10 my-8">
        <h1 class="text-3xl sm:text-4xl font-bold text-center text-gray-800 mb-6">Smart Doc Checker Agent</h1>
        <p class="text-center text-gray-500 mb-8">Upload multiple text documents to analyze them for contradictions and inconsistencies.</p>

        {% if not results %}
        <form id="uploadForm" action="{{ url_for('check_docs') }}" method="post" enctype="multipart/form-data" class="flex flex-col items-center">
            <label for="file-upload" class="cursor-pointer bg-blue-50 hover:bg-blue-100 text-blue-600 font-semibold py-3 px-6 rounded-lg border-2 border-blue-200 border-dashed transition-colors duration-200 w-full text-center">
                <span id="file-label" class="block">Click to select documents (or drag & drop)</span>
                <input id="file-upload" type="file" name="files[]" multiple class="hidden" onchange="updateFileName()">
            </label>
            <button type="submit" class="mt-6 w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
                Analyze Documents
            </button>
        </form>

        <div id="loading" class="hidden mt-8 flex flex-col items-center justify-center">
            <div class="spinner"></div>
            <p class="mt-4 text-gray-500 text-center">Analyzing documents for contradictions...</p>
        </div>
        {% else %}
        <div class="mt-8">
            <h2 class="text-2xl font-bold text-gray-700 mb-4">Analysis Results</h2>
            <div class="bg-gray-50 rounded-lg p-6 border border-gray-200">
                {% if results.error %}
                <p class="text-red-500 font-semibold mb-2">Error:</p>
                <p class="text-red-500 whitespace-pre-line">{{ results.error }}</p>
                {% else %}
                <p class="text-gray-700 whitespace-pre-line">{{ results.content }}</p>
                {% endif %}
            </div>
            <div class="mt-8 text-center">
                <a href="{{ url_for('index') }}" class="inline-block bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded-lg transition-colors duration-200">
                    Go Back
                </a>
            </div>
        </div>
        {% endif %}
    </div>

    <script>
        document.getElementById('uploadForm').addEventListener('submit', function() {
            document.getElementById('uploadForm').classList.add('hidden');
            document.getElementById('loading').classList.remove('hidden');
        });

        function updateFileName() {
            const fileInput = document.getElementById('file-upload');
            const fileLabel = document.getElementById('file-label');
            if (fileInput.files.length > 0) {
                if (fileInput.files.length === 1) {
                    fileLabel.textContent = fileInput.files[0].name;
                } else {
                    fileLabel.textContent = fileInput.files.length + ' files selected';
                }
                document.getElementById('file-label').classList.remove('text-blue-600');
                document.getElementById('file-label').classList.add('text-gray-800');
            }
        }
    </script>
</body>
</html>
"""

# IMPORTANT: You must replace "YOUR_API_KEY_HERE" with your actual Gemini API key.
API_KEY = "AIzaSyCxN2S2OTjdAd5cz4u6ZkteqLav0cXkUPg"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key=" + API_KEY

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, title="Doc Checker", results=None)

@app.route('/check-docs', methods=['POST'])
def check_docs():
    # Check if the API key has been set
    if API_KEY == "YOUR_API_KEY_HERE":
        return render_template_string(HTML_TEMPLATE, title="Results", results={"error": "API key not set. Please update the API_KEY variable in the app.py file."})

    # Check if a file was uploaded
    if 'files[]' not in request.files or not request.files.getlist('files[]'):
        return render_template_string(HTML_TEMPLATE, title="Results", results={"error": "No files uploaded. Please select one or more text documents."})

    uploaded_files = request.files.getlist('files[]')
    
    # Read content from each document
    documents_content = ""
    for file in uploaded_files:
        if file.filename != '':
            # Basic check to ensure it's a text file
            filename = secure_filename(file.filename)
            if not filename.endswith(('.txt', '.md', '.log')):
                return render_template_string(HTML_TEMPLATE, title="Results", results={"error": f"File '{filename}' is not a supported text format. Please upload .txt, .md, or .log files."})
            
            try:
                content = file.read().decode('utf-8')
                documents_content += f"--- Document: {filename} ---\n{content}\n\n"
            except Exception as e:
                # Log the error but continue with other files
                print(f"Error reading file {filename}: {e}")
                return render_template_string(HTML_TEMPLATE, title="Results", results={"error": f"Error reading file '{filename}'. Please ensure it is a valid UTF-8 encoded text file."})
    
    if not documents_content.strip():
        return render_template_string(HTML_TEMPLATE, title="Results", results={"error": "The uploaded files are empty or could not be read."})

    # Prepare the payload for the Gemini API call
    system_prompt = "You are a Smart Document Checker Agent. Your task is to analyze multiple documents and identify any factual contradictions or inconsistencies. Report the findings clearly and concisely. If there are no contradictions, state that the documents are consistent."
    user_query = f"Analyze the following documents for contradictions:\n\n{documents_content}"
    
    # Print the user query to the console for debugging purposes
    print("Sending the following query to the API:")
    print("---")
    print(user_query)
    print("---")
    
    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
    }

    results = {"content": "An unexpected error occurred."}

    try:
        response = requests.post(API_URL, json=payload, timeout=60)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        
        api_response = response.json()
        
        if api_response.get("candidates") and api_response["candidates"][0].get("content"):
            generated_text = api_response["candidates"][0]["content"]["parts"][0]["text"]
            results["content"] = generated_text
        else:
            results["error"] = "No content was generated. The documents may be too complex or an API error occurred. API Response: " + json.dumps(api_response)
            print("API Response Error:", api_response)

    except requests.exceptions.HTTPError as e:
        results["error"] = f"HTTP Error: {e.response.status_code} - {e.response.text}"
        print("API HTTP Exception:", e.response.status_code, e.response.text)
    except requests.exceptions.RequestException as e:
        results["error"] = f"An API request error occurred: {e}"
        print("API Request Exception:", e)

    return render_template_string(HTML_TEMPLATE, title="Results", results=results)

if __name__ == '__main__':
    app.run(debug=True)