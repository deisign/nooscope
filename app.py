import os
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
import requests
import praw
import feedparser
from pytrends.request import TrendReq

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Debug: Log environment variables to check loading
print("DEBUG: Environment variables loaded:")
print("REDDIT_CLIENT_ID:", os.getenv("REDDIT_CLIENT_ID"))
print("REDDIT_CLIENT_SECRET:", os.getenv("REDDIT_CLIENT_SECRET"))
print("REDDIT_USER_AGENT:", os.getenv("REDDIT_USER_AGENT"))
print("NEWS_API_KEY:", os.getenv("NEWS_API_KEY"))

# News API Configuration
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/everything"

# Reddit API Configuration
REDDIT = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

# RSS Feed URLs for Russia and Ukraine
RSS_FEEDS = {
    "russia": "http://feeds.bbci.co.uk/news/world-europe-17839672/rss.xml",
    "ukraine": "http://feeds.bbci.co.uk/news/world-europe-18027962/rss.xml"
}

@app.route('/')
def home():
    """Render the main HTML page."""
    return render_template('index.html')

@app.route('/news', methods=['GET'])
def get_news():
    """Fetch news articles for a specific topic."""
    query = request.args.get("query", "Ukraine")
    url = f"{NEWS_API_URL}?q={query}&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    data = response.json()
    articles = [{"title": article["title"], "url": article["url"]} for article in data.get("articles", [])]
    return jsonify(articles)

@app.route('/rss', methods=['GET'])
def get_rss():
    """Fetch RSS feed data for Russia or Ukraine."""
    country = request.args.get("country", "russia")
    feed_url = RSS_FEEDS.get(country, RSS_FEEDS["russia"])
    feed = feedparser.parse(feed_url)
    items = [{"title": entry.title, "link": entry.link} for entry in feed.entries[:10]]
    return jsonify(items)

@app.route('/reddit', methods=['GET'])
def get_reddit_trends():
    """Fetch trending posts from Reddit."""
    subreddit = request.args.get("subreddit", "worldnews")
    trends = []
    try:
        for s
