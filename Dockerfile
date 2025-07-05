FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y wget unzip curl gnupg

# Install Google Chrome stable (fixed version)
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb || apt-get -f install -y

# Install matching ChromeDriver (change version if you update Chrome)
RUN wget -q https://chromedriver.storage.googleapis.com/117.0.5938.62/chromedriver_linux64.zip && \
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
