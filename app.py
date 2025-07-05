from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import json
import time
import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or "YOUR_API_KEY"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

app = Flask(__name__)

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.binary_location = "/usr/bin/chromium"  # Adjust if needed
    return webdriver.Chrome(options=chrome_options)

def fetch_text_from_url(driver, url):
    try:
        driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()
        return ' '.join(soup.stripped_strings)
    except Exception as e:
        return f"Error fetching content: {str(e)}"

def compare_pdps(your_text, comp_text):
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': GEMINI_API_KEY
    }
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"""
You are an expert in e-commerce product marketing.
Compare two product display pages (PDPs) and provide:
1. Features present on the competitor's PDP but missing on ours.
2. Visual and messaging differences.
3. Suggestions to improve our PDP.

Our PDP content:
{your_text[:4000]}

Competitor's PDP content:
{comp_text[:4000]}
                        """
                    }
                ]
            }
        ]
    }
    response = requests.post(GEMINI_ENDPOINT, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        return f"Error: {response.status_code} - {response.text}"

@app.route('/', methods=['GET', 'POST'])
def index():
    result = ''
    if request.method == 'POST':
        your_url = request.form['your_url']
        comp_url = request.form['comp_url']
        driver = init_driver()
        your_text = fetch_text_from_url(driver, your_url)
        comp_text = fetch_text_from_url(driver, comp_url)
        driver.quit()
        result = compare_pdps(your_text, comp_text)
    return render_template('index.html', result=result)

# ✅ Render requires you to bind to 0.0.0.0 and use the $PORT environment variable
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
