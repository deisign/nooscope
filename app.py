import os
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
import requests
import praw
import feedparser

# Load environment variables
load_dotenv()

app = Flask(__name__)

# News API Configuration
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

# Reddit API Configuration
REDDIT = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

# RSS Feed URLs
RSS_FEEDS = {
    "general": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "technology": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "world": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
}

@app.route('/')
def home():
    """Render the main HTML page."""
    return render_template('index.html')

@app.route('/rss', methods=['GET'])
def get_rss():
    """Fetch and return RSS feed data."""
    category = request.args.get("category", "general")
    feed_url = RSS_FEEDS.get(category, RSS_FEEDS["general"])
    feed = feedparser.parse(feed_url)
    items = [{"title": entry.title, "link": entry.link} for entry in feed.entries[:10]]
    return jsonify(items)

@app.route('/news', methods=['GET'])
def get_news():
    """Fetch news articles based on a query."""
    query = request.args.get("query", "technology")
    url = f"{NEWS_API_URL}?q={query}&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    data = response.json()
    articles = [{"title": article["title"], "url": article["url"]} for article in data.get("articles", [])]
    return jsonify(articles)

@app.route('/reddit', methods=['GET'])
def get_reddit_trends():
    """Fetch trending posts from a subreddit."""
    subreddit = request.args.get("subreddit", "all")
    trends = []
    try:
        for submission in REDDIT.subreddit(subreddit).hot(limit=10):
            trends.append({"title": submission.title, "url": submission.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(trends)

@app.route('/google-trends', methods=['GET'])
def get_google_trends():
    """Placeholder for Google Trends API integration."""
    return jsonify({"message": "Google Trends API integration coming soon!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
