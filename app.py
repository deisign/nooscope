import os
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
import requests
import praw
import feedparser
from pytrends.request import TrendReq
from textblob import TextBlob
from time import time

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

    if reddit_trends_cache["data"] and (current_time - reddit_trends_cache["timestamp"] < CACHE_EXPIRY):
        return jsonify(reddit_trends_cache["data"])

    trends = []
    try:
        for submission in REDDIT.subreddit("all").hot(limit=10):
            sentiment = TextBlob(submission.title).sentiment.polarity
            trends.append({"title": submission.title, "url": submission.url, "sentiment": sentiment})
        reddit_trends_cache = {"data": trends, "timestamp": current_time}
    except Exception as e:
        return jsonify({"error": f"Reddit error: {e}"}), 500
    return jsonify(trends)

@app.route('/news-headlines', methods=['GET'])
def get_news_headlines():
    """Fetch top news headlines."""
    try:
        response = requests.get(f"{NEWS_API_URL}?country=us&apiKey={NEWS_API_KEY}")
        response.raise_for_status()
        data = response.json()
        articles = [
            {
                "title": article["title"],
                "url": article["url"],
                "sentiment": TextBlob(article["title"]).sentiment.polarity
            }
            for article in data.get("articles", [])
        ]
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"News API error: {e}"}), 500
    return jsonify(articles)

@app.route('/rss-feed', methods=['GET'])
def get_rss_feed():
    """Fetch RSS feeds for Russia and Ukraine."""
    feeds = {}
    try:
        for country, url in RSS_FEEDS.items():
            feed = feedparser.parse(url)
            if feed.entries:
                feeds[country] = [
                    {
                        "title": entry.title,
                        "link": entry.link,
                        "sentiment": TextBlob(entry.title).sentiment.polarity
                    }
                    for entry in feed.entries[:5]
                ]
            else:
                feeds[country] = [{"title": "No data available", "link": "#", "sentiment": None}]
    except Exception as e:
        return jsonify({"error": f"RSS error: {e}"}), 500
    return jsonify(feeds)

@app.route('/google-trends', methods=['GET'])
def get_google_trends():
    """Fetch trending searches from Google Trends."""
    global google_trends_cache
    current_time = time()

    # Check cache validity
    if google_trends_cache["data"] and (current_time - google_trends_cache["timestamp"] < CACHE_EXPIRY):
        return jsonify(google_trends_cache["data"])

    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        trending_searches = pytrends.trending_searches()
        trends = [
            {
                "rank": idx + 1,
                "topic": row[0],
                "sentiment": TextBlob(row[0]).sentiment.polarity
            }
            for idx, row in trending_searches.iterrows()
        ]

        # Cache the results
        google_trends_cache = {"data": trends, "timestamp": current_time}
        return jsonify(trends)
    except Exception as e:
        print(f"Error fetching Google Trends data: {e}")
        return jsonify({"error": f"Google Trends error: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
