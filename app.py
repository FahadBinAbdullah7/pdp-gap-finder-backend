from flask import Flask, render_template, request, session
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import json
import time
import os
import pdfplumber
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or "YOUR_API_KEY"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"  # Updated to gemini-pro (verify with Google API docs)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your-secret-key")  # Required for session

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
    try:
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("Selenium WebDriver initialized successfully")
        return driver
    except Exception as e:
        logger.error(f"Error initializing WebDriver: {str(e)}")
        raise

# Fetch text from a URL
def fetch_text_from_url(driver, url):
    try:
        driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()
        text = ' '.join(soup.stripped_strings)
        logger.info(f"Fetched content from {url}")
        return text
    except Exception as e:
        logger.error(f"Error fetching content from {url}: {str(e)}")
        return f"Error fetching content: {str(e)}"

# Extract text from a PDF file
def extract_pdf_text(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        logger.info("PDF text extracted successfully")
        return text
    except Exception as e:
        logger.error(f"Error extracting PDF: {str(e)}")
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
OPSIS

    try:
        response = requests.post(GEMINI_ENDPOINT, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()['candidates'][0]['content']['parts'][0]['text']
        logger.info("PDP comparison successful")
        return result
    except (requests.RequestException, KeyError, IndexError) as e:
        logger.error(f"Error in PDP comparison: {str(e)}")
        return f"Error in Gemini API: {str(e)}"

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
    try:
        response = requests.post(GEMINI_ENDPOINT, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()['candidates'][0]['content']['parts'][0]['text']
        logger.info("SEO keywords generated successfully")
        return result
    except (requests.RequestException, KeyError, IndexError) as e:
        logger.error(f"Error generating SEO keywords: {str(e)}")
        return f"Error in Gemini API: {str(e)}"

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
    try:
        response = requests.post(GEMINI_ENDPOINT, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()['candidates'][0]['content']['parts'][0]['text']
        logger.info("PDP description generated successfully")
        return result
    except (requests.RequestException, KeyError, IndexError) as e:
        logger.error(f"Error generating PDP description: {str(e)}")
        return f"Error in Gemini API: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def index():
    # Initialize result dictionary, load from session if available
    result = session.get('result', {
        'pdp_analysis': '',
        'seo_keywords': '',
        'pdp_description': '',
        'program': '',
        'pdf_text': '',
        'your_url': '',
        'comp_url': '',
        'error': ''
    })

    if request.method == 'POST':
        action = request.form.get('action')
        logger.info(f"Received POST request with action: {action}")

        if action == 'compare':
            # Step 1: Compare PDPs
            your_url = request.form.get('your_url')
            comp_url = request.form.get('comp_url')
            if not your_url or not comp_url:
                result['error'] = "Please provide both URLs"
                logger.warning("Missing URLs in compare action")
            else:
                try:
                    driver = init_driver()
                    your_text = fetch_text_from_url(driver, your_url)
                    comp_text = fetch_text_from_url(driver, comp_url)
                    driver.quit()
                    result['pdp_analysis'] = compare_pdps(your_text, comp_text)
                    result['your_url'] = your_url
                    result['comp_url'] = comp_url
                except Exception as e:
                    result['error'] = f"Error in PDP comparison: {str(e)}"
                    logger.error(f"PDP comparison failed: {str(e)}")
        
        elif action == 'upload':
            # Step 2: Handle PDF upload
            if 'pdf_file' not in request.files:
                result['error'] = "No PDF file uploaded"
                logger.warning("No PDF file uploaded")
            else:
                pdf_file = request.files['pdf_file']
                if pdf_file.filename == '':
                    result['error'] = "No PDF file selected"
                    logger.warning("No PDF file selected")
                else:
                    pdf_text = extract_pdf_text(pdf_file)
                    result['pdf_text'] = pdf_text
                    result['pdp_analysis'] = request.form.get('pdp_analysis', '')
                    logger.info("PDF uploaded and processed")
        
        elif action == 'generate_seo':
            # Step 3: Generate SEO keywords
            program = request.form.get('program')
            pdp_analysis = request.form.get('pdp_analysis', '')
            if not program:
                result['error'] = "Please specify a program"
                logger.warning("No program specified")
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
            if not all([program, pdf_text, seo_keywords, pdp_analysis]):
                result['error'] = "Missing required data for PDP generation"
                logger.warning("Missing data for PDP generation")
            else:
                result['pdp_description'] = generate_pdp_description(program, pdf_text, seo_keywords, pdp_analysis)
                result['program'] = program
                result['seo_keywords'] = seo_keywords
                result['pdp_analysis'] = pdp_analysis
                logger.info("PDP description generated")
        
        else:
            result['error'] = f"Invalid action: {action}"
            logger.error(f"Invalid action: {action}")

        # Store result in session
        session['result'] = result

    return render_template('index.html', result=result)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
