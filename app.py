import os
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import requests
import praw

load_dotenv()

app = Flask(__name__)

# News API Configuration
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

# Reddit Configuration
REDDIT = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

@app.route('/news', methods=['GET'])
def get_news():
    query = request.args.get("query", "technology")
    url = f"{NEWS_API_URL}?q={query}&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    return jsonify(response.json())

@app.route('/reddit', methods=['GET'])
def get_reddit_trends():
    subreddit = request.args.get("subreddit", "all")
    trends = []
    for submission in REDDIT.subreddit(subreddit).hot(limit=10):
        trends.append({"title": submission.title, "url": submission.url})
    return jsonify(trends)

@app.route('/google-trends', methods=['GET'])
def get_google_trends():
    # Placeholder for Google Trends API
    return jsonify({"message": "Google Trends API integration coming soon!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
