from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
import sqlite3
import os
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
REDDIT = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)
RSS_FEEDS = {
    "russia": "http://feeds.bbci.co.uk/news/world-europe-17839672/rss.xml",
    "ukraine": "http://feeds.bbci.co.uk/news/world-europe-18027962/rss.xml"
}

DATABASE = "nooscope.db"

# Cache for Google Trends
google_trends_cache = {"data": None, "timestamp": 0}
CACHE_EXPIRY = 3600  # 1 hour


def init_db():
    """Initialize the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                topic TEXT,
                sentiment REAL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("Database initialized: 'trends' table created or already exists.")
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()


def save_to_db(source, topic, sentiment):
    """Save trend data to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO trends (source, topic, sentiment) VALUES (?, ?, ?)", (source, topic, sentiment))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving to database: {e}")
    finally:
        conn.close()


@app.route('/')
def index():
    """Render the main dashboard."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Fetch data for display
    cursor.execute("SELECT topic, sentiment, date FROM trends WHERE source = 'RSS Feed'")
    rss_data = cursor.fetchall()
    cursor.execute("SELECT topic, sentiment, date FROM trends WHERE source = 'Google Trends'")
    google_data = cursor.fetchall()
    cursor.execute("SELECT topic, sentiment, date FROM trends WHERE source = 'Reddit Trends'")
    reddit_data = cursor.fetchall()

    conn.close()

    return render_template('index.html', rss_data=rss_data, google_data=google_data, reddit_data=reddit_data)


@app.route('/fetch-data', methods=['GET'])
def fetch_data():
    """Fetch data from all sources and save to the database."""
    try:
        # RSS Feeds
        for source, url in RSS_FEEDS.items():
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                sentiment = TextBlob(entry.title).sentiment.polarity
                save_to_db("RSS Feed", entry.title, sentiment)

        # Google Trends
        pytrends = TrendReq(hl='en-US', tz=360)
        trending_searches = pytrends.trending_searches()
        for _, row in trending_searches.iterrows():
            topic = row[0]
            sentiment = TextBlob(topic).sentiment.polarity
            save_to_db("Google Trends", topic, sentiment)

        # Reddit Trends
        for submission in REDDIT.subreddit("all").hot(limit=10):
            sentiment = TextBlob(submission.title).sentiment.polarity
            save_to_db("Reddit Trends", submission.title, sentiment)

        return jsonify({"status": "Data fetched and saved successfully"})
    except Exception as e:
        return jsonify({"error": f"Error fetching data: {e}"}), 500


@app.route('/check-db', methods=['GET'])
def check_db():
    """Check if the database and table exist."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trends';")
        table_exists = cursor.fetchone()
        if table_exists:
            return jsonify({"status": "Table 'trends' exists in the database."})
        else:
            return jsonify({"error": "Table 'trends' does not exist."}), 500
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    init_db()  # Ensure the database and table exist
    app.run(host='0.0.0.0', port=5000)
