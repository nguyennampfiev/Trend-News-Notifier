from __future__ import annotations

import os
from datetime import datetime

import requests
from dotenv import load_dotenv  # Import the function
from mcp.server.fastmcp import FastMCP

load_dotenv()

api_key = os.getenv("SERPAPI_KEY")
mcp = FastMCP("serpapisearch", port=8001)


def search_hot_news(api_key, query, language="en", timeframe="24h", num_results=20):
    """
    Search for hot/trending news using SerpAPI

    Args:
        api_key (str): SerpAPI key
        query (str): Search query
        language (str): Language code
        timeframe (str): "1h", "24h", "7d", "1m", "1y" or custom date
        num_results (int): Number of results

    Returns:
        List[Dict]: Hot news articles
    """

    base_url = "https://serpapi.com/search"

    # Time-based parameters for hot news
    tbs_map = {
        "1h": "qdr:h",  # Past hour
        "24h": "qdr:d",  # Past day
        "7d": "qdr:w",  # Past week
        "1m": "qdr:m",  # Past month
        "1y": "qdr:y",  # Past year
    }

    params = {
        "api_key": api_key,
        "engine": "google",
        "q": query,
        "tbm": "nws",  # News search
        "num": num_results,
        "hl": language,
        "gl": "us",
        "safe": "active",
        "tbs": tbs_map.get(timeframe, "qdr:d"),  # Time filter for hot news
        "sort": "date",  # Sort by recency for hot news
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract hot news with focus on trending indicators
        articles = []
        for item in data.get("news_results", []):

            # Calculate recency score (newer = hotter)
            published_at = item.get("date")
            recency_score = calculate_recency_score(published_at)

            article = {
                "id": item.get("link"),
                "source": item.get("source", ""),
                "url": item.get("link"),
                "title": item.get("title", ""),
                "content": item.get("snippet", ""),
                "published_at": published_at,
                "language": language,
                # HOT NEWS specific fields
                "recency_score": recency_score,  # How recent (higher = newer)
                "source_authority": get_source_authority(
                    item.get("source", "")
                ),  # Source credibility
                "engagement_keywords": extract_hot_keywords(
                    item.get("title", "") + " " + item.get("snippet", "")
                ),
                "is_breaking": is_breaking_news(item.get("title", "")),
                "search_query": query,  # What query found this
                "search_timestamp": datetime.now().isoformat(),  # When we found it
            }

            articles.append(article)

        # Sort by hotness (recency + authority + breaking news)
        articles.sort(
            key=lambda x: (
                x["is_breaking"] * 10
                + x["recency_score"]  # Breaking news gets priority
                + x["source_authority"]  # Recent news  # Authoritative sources
            ),
            reverse=True,
        )

        return articles

    except requests.exceptions.RequestException as e:
        print(f"Error searching hot news: {e}")
        return []


def calculate_recency_score(published_date_str):
    """Calculate how recent the news is (0-10 scale)"""
    if not published_date_str:
        return 0

    try:
        # Parse different date formats from Google News
        from dateutil import parser

        published_date = parser.parse(published_date_str)
        now = datetime.now(published_date.tzinfo)

        hours_ago = (now - published_date).total_seconds() / 3600

        if hours_ago <= 1:
            return 10  # Within 1 hour = super hot
        elif hours_ago <= 6:
            return 8  # Within 6 hours = very hot
        elif hours_ago <= 24:
            return 6  # Within 24 hours = hot
        elif hours_ago <= 168:  # 1 week
            return 3  # Within week = warm
        else:
            return 1  # Older = cold

    except Exception:
        return 0


def get_source_authority(source):
    """Rate source authority/credibility (0-5 scale)"""
    # Major news sources get higher authority scores
    high_authority = [
        "reuters",
        "ap",
        "bbc",
        "cnn",
        "nytimes",
        "washingtonpost",
        "wsj",
        "bloomberg",
        "npr",
        "abc",
        "cbs",
        "nbc",
    ]
    medium_authority = [
        "fox",
        "usa today",
        "guardian",
        "independent",
        "time",
        "newsweek",
        "politico",
        "axios",
    ]

    source_lower = source.lower()

    for auth_source in high_authority:
        if auth_source in source_lower:
            return 5

    for auth_source in medium_authority:
        if auth_source in source_lower:
            return 3

    return 1  # Unknown sources get low score


def extract_hot_keywords(text):
    """Extract keywords that indicate trending/hot news"""
    hot_indicators = [
        "breaking",
        "urgent",
        "just in",
        "developing",
        "latest",
        "update",
        "now",
        "today",
        "happening",
        "live",
        "exclusive",
        "first",
        "new",
        "trending",
        "viral",
        "surge",
        "spike",
        "boom",
        "crisis",
        "alert",
    ]

    text_lower = text.lower()
    found_keywords = [keyword for keyword in hot_indicators if keyword in text_lower]
    return found_keywords


def is_breaking_news(title):
    """Check if this appears to be breaking news"""
    breaking_indicators = ["breaking", "urgent", "just in", "developing", "alert"]
    title_lower = title.lower()
    return any(indicator in title_lower for indicator in breaking_indicators)


@mcp.tool(
    name="search_trending_topics", description="Search for trending topics wih serpapi"
)
def search_trending_topics(topics="breaking news", language="en"):
    """Search for trending topics
    Args:
        api_key (str): Your SerpAPI key
        topic (str): Specific topic to search for, or None for general trending
        language (str): Language code (default: "en")

    Returns:
        List[Dict]: Trending news articles
    """

    if topics is None:
        topics = [
            "breaking news",
            "trending now",
            "latest news",
            "developing story",
            "just happened",
        ]

    all_hot_articles = []
    for topic in topics:
        articles = search_hot_news(
            api_key, topic, language, timeframe="24h", num_results=10
        )
        all_hot_articles.extend(articles)

    # Remove duplicates by URL
    seen_urls = set()
    unique_articles = []
    for article in all_hot_articles:
        if article["url"] not in seen_urls:
            seen_urls.add(article["url"])
            unique_articles.append(article)

    return unique_articles


@mcp.tool(
    name="search_by_categoty_hot_news",
    description="Search hot news by category with serpapi",
)
def search_by_category_hot_news(category="politics", language="en"):
    """Search hot news by category
    Args:
        category (str): Category to search for (e.g., "politics", "technology")
        language (str): Language code (default: "en")

    Returns:
        List[Dict]: Hot news articles in the specified category
    """

    category_queries = {
        "politics": "politics breaking news latest",
        "technology": "tech news latest breakthrough",
        "business": "business news market latest",
        "sports": "sports news latest scores",
        "entertainment": "entertainment news celebrity latest",
        "health": "health news medical breakthrough",
        "science": "science news discovery latest",
        "world": "world news international breaking",
    }

    query = category_queries.get(category, f"{category} latest news")
    return search_hot_news(api_key, query, language, timeframe="24h")


if __name__ == "__main__":
    mcp.run(transport="stdio")
