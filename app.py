import os
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
import requests
import praw
import feedparser
from pytrends.request import TrendReq
from time import time, sleep

# Load environment variables
load_dotenv()

app = Flask(__name__)

# API Configuration
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

REDDIT = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

RSS_FEEDS = {
    "russia": "http://feeds.bbci.co.uk/news/world-europe-17839672/rss.xml",
    "ukraine": "http://feeds.bbci.co.uk/news/world-europe-18027962/rss.xml"
}

# Cache for Reddit and Google Trends
reddit_trends_cache = {"data": None, "timestamp": 0}
google_trends_cache = {"data": None, "timestamp": 0}
CACHE_EXPIRY = 3600  # Cache expiry in seconds (1 hour)

@app.route('/')
def home():
    """Render the main dashboard."""
    return render_template('index.html')

@app.route('/reddit-trends', methods=['GET'])
def get_reddit_trends():
    """Fetch top trending posts from Reddit with caching."""
    global reddit_trends_cache
    current_time = time()

    # Check cache validity
    if reddit_trends_cache["data"] and (current_time - reddit_trends_cache["timestamp"] < CACHE_EXPIRY):
        print("Returning cached Reddit trends data.")
        return jsonify(reddit_trends_cache["data"])

    trends = []
    try:
        for submission in REDDIT.subreddit("all").hot(limit=10):
            trends.append({"title": submission.title, "url": submission.url})
        reddit_trends_cache = {"data": trends, "timestamp": current_time}  # Update cache
        print("Reddit trends fetched successfully.")
    except Exception as e:
        print(f"Error fetching Reddit trends: {e}")
        return jsonify({"error": "Unable to fetch Reddit trends. Check API limits or credentials."}), 500
    return jsonify(trends)

@app.route('/news-headlines', methods=['GET'])
def get_news_headlines():
    """Fetch top news headlines."""
    try:
        response = requests.get(f"{NEWS_API_URL}?country=us&apiKey={NEWS_API_KEY}")
        response.raise_for_status()
        data = response.json()
        articles = [{"title": article["title"], "url": article["url"]} for article in data.get("articles", [])]
        print("News headlines fetched successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news headlines: {e}")
        return jsonify({"error": "Unable to fetch news headlines. Check API key or limits."}), 500
    return jsonify(articles)

@app.route('/rss-feed', methods=['GET'])
def get_rss_feed():
    """Fetch RSS feeds for Russia and Ukraine."""
    feeds = {}
    try:
        for country, url in RSS_FEEDS.items():
            feed = feedparser.parse(url)
            feeds[country] = [{"title": entry.title, "link": entry.link} for entry in feed.entries[:5]]
            print(f"RSS feed for {country} fetched successfully.")
    except Exception as e:
        print(f"Error fetching RSS feeds: {e}")
        return jsonify({"error": str(e)}), 500
    return jsonify(feeds)

@app.route('/google-trends', methods=['GET'])
def get_google_trends():
    """Fetch Google Trends data for Ukraine and Russia with caching."""
    global google_trends_cache
    current_time = time()

    # Check cache validity
    if google_trends_cache["data"] and (current_time - google_trends_cache["timestamp"] < CACHE_EXPIRY):
        print("Returning cached Google Trends data.")
        return jsonify(google_trends_cache["data"])

    try:
        sleep(5)  # Задержка для предотвращения блокировки
        pytrends = TrendReq()
        pytrends.build_payload(kw_list=["Ukraine", "Russia"], geo="UA", timeframe="now 7-d")
        trends = pytrends.interest_over_time()

        if not trends.empty:
            # Преобразование ключей Timestamp в строковый формат
            data = {
                timestamp.strftime("%Y-%m-%d %H:%M:%S"): values.to_dict()
                for timestamp, values in trends.iterrows()
            }
            google_trends_cache = {"data": data, "timestamp": current_time}  # Обновление кэша
            print("Google Trends data fetched successfully.")
            return jsonify(data)
    except Exception as e:
        print(f"Error fetching Google Trends: {e}")
        return jsonify({"error": "Unable to fetch Google Trends data. Check request parameters or try again later."}), 500

    return jsonify({"message": "No data available"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
