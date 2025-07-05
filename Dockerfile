FROM python:3.10-slim

# Install required system packages
RUN apt-get update && apt-get install -y wget unzip curl gnupg libglib2.0-0 libnss3 libgconf-2-4 libxss1 libappindicator3-1 libasound2 libatk-bridge2.0-0 libgtk-3-0 libxrandr2 libgbm1 xdg-utils fonts-liberation ca-certificates

# Install Google Chrome v138.0.7204.93
RUN wget https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_138.0.7204.93-1_amd64.deb && \
    dpkg -i google-chrome-stable_138.0.7204.93-1_amd64.deb || apt-get -f install -y

# Install ChromeDriver v138.0.7204.93 (matching Chrome)
RUN wget https://chromedriver.storage.googleapis.com/138.0.7204.93/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver

# Setup working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . .

# Environment config for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

# Start the Flask server
CMD ["python", "app.py"]
