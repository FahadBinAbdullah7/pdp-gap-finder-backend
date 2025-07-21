from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import json
import time
import os
import pdfplumber

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or "YOUR_API_KEY"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

app = Flask(__name__)

# Initialize Selenium WebDriver
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.binary_location = "/usr/bin/chromium"
    return webdriver.Chrome(options=chrome_options)

# Fetch text from a URL
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

# Extract text from a PDF file
def extract_pdf_text(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

# Compare PDPs using Gemini API
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
You are an expert in ed-tech product marketing.
Compare two product display pages (PDPs) and provide:
1. Features present on the competitor's PDP but missing on ours.
2. Visual and messaging differences.
3. Areas where our PDP is stronger or more effective than the competitor's (e.g., content, structure, call-to-action, credibility, design).
4. Suggestions to improve our PDP.

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
        try:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            return "Error: Unexpected response format from Gemini API"
    else:
        return f"Error: {response.status_code} - {response.text}"

# Generate SEO keywords using Gemini API
def generate_seo_keywords(program, pdp_analysis):
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
You are an SEO expert for ed-tech products. Based on the following program and PDP analysis, suggest 5-10 SEO keywords to optimize a new PDP.

Program: {program}
PDP Analysis: {pdp_analysis[:2000]}
                        """
                    }
                ]
            }
        ]
    }
    response = requests.post(GEMINI_ENDPOINT, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        try:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            return "Error: Unexpected response format from Gemini API"
    else:
        return f"Error: {response.status_code} - {response.text}"

# Generate new PDP description using Gemini API
def generate_pdp_description(program, pdf_text, seo_keywords, pdp_analysis):
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': GEMINI_API_KEY
    }
    template = """
**Headline**: [Catchy headline incorporating program and SEO keywords]
**Introduction**: [Brief overview of the program, 2-3 sentences]
**Key Features**:
- [Feature 1 with benefit]
- [Feature 2 with benefit]
- [Feature 3 with benefit]
**Benefits**: [Why this program stands out, 2-3 sentences]
**Call to Action**: [Clear, compelling CTA]
"""
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"""
You are an expert in ed-tech product marketing. Create a new PDP description for the following program, incorporating the provided PDF content, SEO keywords, and insights from the PDP analysis. Use the following template:

{template}

Program: {program}
PDF Content: {pdf_text[:2000]}
SEO Keywords: {seo_keywords}
PDP Analysis: {pdp_analysis[:2000]}
                        """
                    }
                ]
            }
        ]
    }
    response = requests.post(GEMINI_ENDPOINT, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        try:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            return "Error: Unexpected response format from Gemini API"
    else:
        return f"Error: {response.status_code} - {response.text}"

@app.route('/', methods=['GET', 'POST'])
def index():
    result = {'pdp_analysis': '', 'seo_keywords': '', 'pdp_description': '', 'program': '', 'error': ''}
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'compare':
            # Step 1: Compare PDPs
            your_url = request.form.get('your_url')
            comp_url = request.form.get('comp_url')
            if not your_url or not comp_url:
                result['error'] = "Please provide both URLs"
            else:
                driver = init_driver()
                your_text = fetch_text_from_url(driver, your_url)
                comp_text = fetch_text_from_url(driver, comp_url)
                driver.quit()
                result['pdp_analysis'] = compare_pdps(your_text, comp_text)
        
        elif action == 'upload':
            # Step 2: Handle PDF upload
            if 'pdf_file' not in request.files:
                result['error'] = "No PDF file uploaded"
            else:
                pdf_file = request.files['pdf_file']
                if pdf_file.filename == '':
                    result['error'] = "No PDF file selected"
                else:
                    pdf_text = extract_pdf_text(pdf_file)
                    result['pdp_analysis'] = request.form.get('pdp_analysis', '')
                    result['pdf_text'] = pdf_text  # Store for later use
        
        elif action == 'generate_seo':
            # Step 3: Generate SEO keywords
            program = request.form.get('program')
            pdp_analysis = request.form.get('pdp_analysis', '')
            if not program:
                result['error'] = "Please specify a program"
            else:
                result['program'] = program
                result['pdp_analysis'] = pdp_analysis
                result['seo_keywords'] = generate_seo_keywords(program, pdp_analysis)
        
        elif action == 'generate_pdp':
            # Step 4: Generate new PDP description
            program = request.form.get('program', '')
            pdf_text = request.form.get('pdf_text', '')
            seo_keywords = request.form.get('seo_keywords', '')
            pdp_analysis = request.form.get('pdp_analysis', '')
            if not all([program, pdf_text, seo_keywords]):
                result['error'] = "Missing required data for PDP generation"
            else:
                result['pdp_description'] = generate_pdp_description(program, pdf_text, seo_keywords, pdp_analysis)
                result['program'] = program
                result['seo_keywords'] = seo_keywords
                result['pdp_analysis'] = pdp_analysis
    
    return render_template('index.html', result=result)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
