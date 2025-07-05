FROM python:3.10-slim

RUN apt-get update && apt-get install -y wget unzip curl gnupg

# Install Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb || apt-get -f install -y

# Install ChromeDriver matching Chrome version with sed extraction
RUN CHROME_VERSION=$(google-chrome --version | sed -E 's/.* ([0-9]+\.[0-9]+\.[0-9]+).*/\1/') && \
    wget -q "https://chromedriver.storage.googleapis.com/${CHROME_VERSION}/chromedriver_linux64.zip" && \
    unzip chromedriver_linux64.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

CMD ["python", "app.py"]
