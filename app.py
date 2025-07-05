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
CORS(app)

class PDPGapFinder:
    def __init__(self, api_key):
        self.api_key = api_key
        self.driver = self._init_driver()

    def _init_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.binary_location = "/usr/bin/google-chrome"

        driver = webdriver.Chrome(
            executable_path="/usr/bin/chromedriver",
            options=chrome_options
        )
        return driver

    def fetch_text_from_url(self, url):
        try:
            self.driver.get(url)
            time.sleep(3)
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            return ' '.join(soup.stripped_strings)
        except Exception as e:
            return f"Error fetching content: {str(e)}"

    def compare_pdps(self, your_text, comp_text):
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key
        }
        prompt = {
            "contents": [{
                "parts": [{
                    "text": f"""
You are an expert in e-commerce product marketing.
Compare two product display pages (PDPs) and provide:
1. Features present in competitor PDP but missing in ours.
2. Visual, messaging, and CTA differences.
3. Actionable improvement suggestions.

Our PDP:
{your_text[:4000]}

Competitor PDP:
{comp_text[:4000]}
"""
                }]
            }]
        }
        r = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            headers=headers,
            data=json.dumps(prompt)
        )
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error from Gemini: {r.status_code} - {r.text}"

# Load Gemini API key from env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gap_finder = PDPGapFinder(GEMINI_API_KEY)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    your_url = data.get("your_url")
    comp_url = data.get("comp_url")

    if not your_url or not comp_url:
        return jsonify({"error": "Missing URLs"}), 400

    your_text = gap_finder.fetch_text_from_url(your_url)
    comp_text = gap_finder.fetch_text_from_url(comp_url)
    result = gap_finder.compare_pdps(your_text, comp_text)
    return jsonify({"result": result})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
