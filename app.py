import os
import time
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

class PDPGapFinder:
    def __init__(self, api_key):
        self.api_key = api_key
        self.driver = self._init_selenium_driver()

    def _init_selenium_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--window-size=1920,1080")
        return webdriver.Chrome(options=chrome_options)

    def fetch_text_from_url(self, url):
        try:
            self.driver.get(url)
            time.sleep(3)  # Wait for JS to load
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()
            return ' '.join(soup.stripped_strings)
        except Exception as e:
            return f"Error fetching content: {str(e)}"

    def compare_pdps(self, your_pdp_text, competitor_pdp_text):
        headers = {
            'Content-Type': 'application/json',
            'X-goog-api-key': self.api_key
        }
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"""
You are an expert in e-commerce product marketing.
Compare two product display pages (PDPs) and provide:
1. A list of product details or features that are present on the competitor's page but missing from ours.
2. Differences in visual presentation, customer messaging, or call-to-action language.
3. Actionable suggestions to improve our PDP based on best practices.

Our PDP content:
{your_pdp_text[:4000]}

Competitor's PDP content:
{competitor_pdp_text[:4000]}
"""
                        }
                    ]
                }
            ]
        }
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            headers=headers,
            data=json.dumps(payload)
        )
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error: {response.status_code} - {response.text}"

# Get API key securely from environment variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise Exception("GEMINI_API_KEY environment variable is not set!")

gap_finder = PDPGapFinder(api_key=GEMINI_API_KEY)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    your_url = data.get('your_url')
    comp_url = data.get('comp_url')

    if not your_url or not comp_url:
        return jsonify({"error": "Both 'your_url' and 'comp_url' are required"}), 400

    try:
        your_text = gap_finder.fetch_text_from_url(your_url)
        comp_text = gap_finder.fetch_text_from_url(comp_url)
        result = gap_finder.compare_pdps(your_text, comp_text)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
