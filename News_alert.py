import os
import json
import requests
from datetime import datetime, timedelta

FINNHUB_API_KEY = os.environ["FINNHUB_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

TICKERS = ["SPRB"]

STATE_FILE = "sent_news.json"


def load_sent_news():
    try:
        with open(STATE_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()


def save_sent_news(sent):
    with open(STATE_FILE, "w") as f:
        json.dump(list(sent)[-500:], f)


def get_news(ticker):
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    url = "https://finnhub.io/api/v1/company-news"

    params = {
        "symbol": ticker,
        "from": str(yesterday),
        "to": str(today),
        "token": FINNHUB_API_KEY
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()

    return response.json()


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": False
    }

    response = requests.post(url, data=data, timeout=20)
    response.raise_for_status()


sent_news = load_sent_news()

for ticker in TICKERS:

    try:
        news = get_news(ticker)

        for article in news:

            article_id = str(article.get("id"))

            if article_id in sent_news:
                continue

            headline = article.get("headline", "No headline")
            source = article.get("source", "Unknown")
            url = article.get("url", "")

            timestamp = article.get("datetime", 0)

            if timestamp:
                published = datetime.utcfromtimestamp(timestamp)
                time_string = published.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                time_string = "Unknown"

            message = (
                f"🚨 {ticker} NEWS\n\n"
                f"{headline}\n\n"
                f"Source: {source}\n"
                f"Published: {time_string}\n\n"
                f"{url}"
            )

            send_telegram(message)
            sent_news.add(article_id)

    except Exception as e:
        print(f"Error checking {ticker}: {e}")

save_sent_news(sent_news)
