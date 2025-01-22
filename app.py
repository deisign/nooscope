import os
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
import requests
import praw
import feedparser
from pytrends.request import TrendReq

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

@app.route('/')
def home():
    """Render the main dashboard."""
    return render_template('index.html')

@app.route('/reddit-trends', methods=['GET'])
def get_reddit_trends():
    """Fetch top trending posts from Reddit."""
    try:
        trends = [{"title": submission.title, "url": submission.url} for submission in REDDIT.subreddit("all").hot(limit=10)]
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(trends)

@app.route('/news-headlines', methods=['GET'])
def get_news_headlines():
    """Fetch top news headlines."""
    try:
        response = requests.get(f"{NEWS_API_URL}?country=us&apiKey={NEWS_API_KEY}")
        data = response.json()
        articles = [{"title": article["title"], "url": article["url"]} for article in data.get("articles", [])]
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(articles)

@app.route('/rss-feed', methods=['GET'])
def get_rss_feed():
    """Fetch RSS feeds for Russia and Ukraine."""
    feeds = {}
    try:
        for country, url in RSS_FEEDS.items():
            feed = feedparser.parse(url)
            feeds[country] = [{"title": entry.title, "link": entry.link} for entry in feed.entries[:5]]
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(feeds)

@app.route('/google-trends', methods=['GET'])
def get_google_trends():
    """Fetch Google Trends data for Ukraine and Russia."""
    try:
        pytrends = TrendReq()
        pytrends.build_payload(kw_list=["Ukraine", "Russia"], geo="UA,RU", timeframe="now 7-d")
        trends = pytrends.interest_over_time()
        if not trends.empty:
            data = trends.to_dict("index")
            return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "No data available"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
