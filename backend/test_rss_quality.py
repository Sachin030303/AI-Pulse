
from app.ingestion.rss_collector import collect_rss_feed

url = "https://huggingface.co/blog/feed.xml"

articles = collect_rss_feed(url)

print("TOTAL ARTICLES:", len(articles))

for article in articles[:5]:
    print("\nTITLE:", article["title"])
    print("URL:", article["url"])
    print("SUMMARY:", article["summary"])
    print("CONTENT:", article["content"])
