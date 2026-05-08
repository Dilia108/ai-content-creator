import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_trending_cybersecurity_topics():
    """
    Fetches trending cybersecurity topics using NewsAPI.
    Returns a list of trending topics.
    """
    api_key = os.getenv("NEWS_API_KEY")
    
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "cybersecurity OR zero trust OR ransomware OR endpoint security",
        "sortBy": "popularity",
        "language": "en",
        "pageSize": 5,
        "apiKey": api_key
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get("status") != "ok":
     print(f"NewsAPI error: {data}")
     return []
    
    topics = []
    for article in data.get("articles", []):
        topics.append({
            "title": article["title"],
            "description": article["description"],
            "source": article["source"]["name"],
            "url": article["url"]
        })
    
    return topics


def pick_best_topic(topics):
    """
    Returns the most relevant topic for content generation.
    """
    if not topics:
        return None
    return topics[0]["title"]