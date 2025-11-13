import feedparser
import time


RSS_FEEDS_TO_MONITOR = [

    "https://techcrunch.com/category/artificial-intelligence/feed/"
]

def fetch_and_parse_feed(feed_url):

    print(f"[INFO] Fetching feed: {feed_url}...")
    try:
        # feedparser handles fetching and parsing the XML
        feed = feedparser.parse(feed_url)

        # Check if the feed was fetched and parsed correctly
        if feed.bozo:
            # bozo=1 means the feed is "ill-formed"
            raise Exception(f"Ill-formed feed. Error: {feed.bozo_exception}")

        if 'entries' not in feed or not feed.entries:
            print(f"[WARN] No entries found in feed: {feed_url}")
            return []

        print(f"[INFO] Found {len(feed.entries)} entries.")

        processed_articles = []
        for entry in feed.entries:

            article_data = {
                "title": entry.get("title", "No Title"),
                "link": entry.get("link", "No Link"),
                "published": entry.get("published", "No Date"),
                "summary": entry.get("summary", "No Summary"),
                "source_url": feed_url
            }
            processed_articles.append(article_data)

        return processed_articles

    except Exception as e:
        print(f"[ERROR] Failed to fetch or parse {feed_url}. Reason: {e}")
        return []

def techcrunch_main_ingestion_loop():
    """
    Main loop to run the ingestion.
    For this example, it just runs once.
    In a real system, this would run on a schedule.
    """
    print("--- TrendScout AI: Starting RSS Ingestion  ---")

    all_new_articles = []
    for feed_url in RSS_FEEDS_TO_MONITOR:
        articles = fetch_and_parse_feed(feed_url)
        all_new_articles.extend(articles)
        time.sleep(1)

    print(f"\n--- Ingestion Complete: Total {len(all_new_articles)} articles fetched ---")



    articleInJsonList = []

    for i, article in enumerate(all_new_articles[:5]): # Print first 5
        '''
        print(f"\nArticle {i+1}:")
        print(f"  Title: {article['title']}")
        print(f"  Link: {article['link']}")
        print(f"  Source: {article['source_url']}")
        '''

        # orginize data into json format
        articleInJson = {
            "title": article['title'],
            "link": article['link'],
            "published": article['published'],
            "summary": article['summary'],
            "source_url": article['source_url']
        }

        articleInJsonList.append(articleInJson)


    return articleInJsonList

if __name__ == "__main__":
    techcrunch_main_ingestion_loop()
