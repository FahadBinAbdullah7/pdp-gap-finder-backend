FROM python:3.10-slim

# Install base dependencies
RUN apt-get update && apt-get install -y wget unzip curl gnupg libnss3 libxss1 libasound2 fonts-liberation libappindicator3-1 libatk-bridge2.0-0 libxrandr2 libgbm1 libgtk-3-0 xdg-utils

# Install Chrome v114
RUN wget https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.90-1_amd64.deb && \
    dpkg -i google-chrome-stable_114.0.5735.90-1_amd64.deb || apt-get -fy install

# Install matching ChromeDriver v114
RUN wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Set environment vars and start
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

CMD ["python", "app.py"]
