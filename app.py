from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import json
import time
import os
import PyPDF2

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or "YOUR_API_KEY"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.binary_location = "/usr/bin/chromium"
    return webdriver.Chrome(options=chrome_options)

def fetch_text_from_url(driver, url):
    driver.get(url)
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    return ' '.join(soup.stripped_strings)

def compare_pdps(your_text, comp_text):
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': GEMINI_API_KEY
    }
    prompt = f"""
You are an expert in ed-tech product marketing.
Compare two product display pages (PDPs) and provide:
1. Features present on the competitor's PDP but missing on ours.
2. Visual and messaging differences.
3. Areas where our PDP is stronger.
4. Suggestions to improve our PDP.

Our PDP content:
{your_text[:4000]}

Competitor's PDP content:
{comp_text[:4000]}
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(GEMINI_ENDPOINT, headers=headers, data=json.dumps(payload))
    return response.json()['candidates'][0]['content']['parts'][0]['text'] if response.status_code == 200 else "Error comparing PDPs"

def extract_pdf_text(filepath):
    text = ""
    with open(filepath, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

def generate_new_pdp(pdf_text, program_name, seo_keywords, previous_analysis):
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': GEMINI_API_KEY
    }
    prompt = f"""
You are a marketing copywriter for an ed-tech company.

- Program: {program_name}
- SEO Keywords: {seo_keywords}
- Existing PDP Description (from PDF): {pdf_text[:3000]}
- Previous PDP Analysis: {previous_analysis}

Based on the above, create a new optimized PDP description. Follow best practices for ed-tech marketing, highlight USPs, include persuasive CTAs, and ensure SEO optimization.
"""
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(GEMINI_ENDPOINT, headers=headers, data=json.dumps(payload))
    return response.json()['candidates'][0]['content']['parts'][0]['text'] if response.status_code == 200 else "Error generating new PDP"

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

@app.route('/generate_pdp', methods=['POST'])
def generate_pdp():
    previous_analysis = request.form['previous_analysis']
    program_name = request.form['program_name']
    seo_keywords = request.form['seo_keywords']
    
    pdf_file = request.files['pdf_file']
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
    pdf_file.save(filepath)
    pdf_text = extract_pdf_text(filepath)
    
    new_pdp = generate_new_pdp(pdf_text, program_name, seo_keywords, previous_analysis)
    
    return render_template('index.html', result=previous_analysis, new_pdp=new_pdp)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
