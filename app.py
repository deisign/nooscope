from flask import Flask, render_template, jsonify
import sqlite3
from pytrends.request import TrendReq
import feedparser
from textblob import TextBlob
import praw
import os

app = Flask(__name__)
DATABASE = 'noscope.db'

# Reddit API setup
REDDIT = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

# RSS feeds setup
RSS_FEEDS = {
    "Russia": "https://news.google.com/rss/search?q=Russia&hl=en-US&gl=US&ceid=US:en",
    "Ukraine": "https://news.google.com/rss/search?q=Ukraine&hl=en-US&gl=US&ceid=US:en"
}

# Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            topic TEXT,
            sentiment REAL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized: 'trends' table created or already exists.")

# Save data to the database
def save_to_db(source, topic, sentiment):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO trends (source, topic, sentiment)
        VALUES (?, ?, ?)
    ''', (source, topic, sentiment))
    conn.commit()
    conn.close()

@app.route('/fetch-data', methods=['GET'])
def fetch_data():
    """Fetch data from all sources and save to the database."""
    init_db()
    errors = []

    # Fetch RSS feeds
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                sentiment = TextBlob(entry.title).sentiment.polarity
                save_to_db("RSS Feed", entry.title, sentiment)
                print(f"Saved RSS: {entry.title} with sentiment {sentiment}")
        except Exception as e:
            error_msg = f"RSS Feed Error ({source}): {e}"
            errors.append(error_msg)
            print(error_msg)

    # Fetch Google Trends
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        trending_searches = pytrends.trending_searches()
        for _, row in trending_searches.iterrows():
            topic = row[0]
            sentiment = TextBlob(topic).sentiment.polarity
            save_to_db("Google Trends", topic, sentiment)
            print(f"Saved Google Trend: {topic} with sentiment {sentiment}")
    except Exception as e:
        error_msg = f"Google Trends Error: {e}"
        errors.append(error_msg)
        print(error_msg)

    # Fetch Reddit trends
    try:
        for submission in REDDIT.subreddit("all").hot(limit=10):
            sentiment = TextBlob(submission.title).sentiment.polarity
            save_to_db("Reddit Trends", submission.title, sentiment)
            print(f"Saved Reddit Trend: {submission.title} with sentiment {sentiment}")
    except Exception as e:
        error_msg = f"Reddit Trends Error: {e}"
        errors.append(error_msg)
        print(error_msg)

    return jsonify({"status": "Data fetched", "errors": errors})

@app.route('/')
def index():
    """Render the main dashboard."""
    init_db()
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT topic, sentiment, date FROM trends WHERE source = 'RSS Feed'")
    rss_data = cursor.fetchall()
    cursor.execute("SELECT topic, sentiment, date FROM trends WHERE source = 'Google Trends'")
    google_data = cursor.fetchall()
    cursor.execute("SELECT topic, sentiment, date FROM trends WHERE source = 'Reddit Trends'")
    reddit_data = cursor.fetchall()
    conn.close()

    return render_template('index.html', rss_data=rss_data, google_data=google_data, reddit_data=reddit_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
