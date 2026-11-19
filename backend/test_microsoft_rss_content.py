from app.ingestion.rss_collector import collect_rss_feed


feed_url = "https://news.microsoft.com/source/topics/ai/feed/"

articles = collect_rss_feed(feed_url)

target = "Copilotforce"

for article in articles:
    if target.lower() in article["title"].lower():
        print("TITLE:", article["title"])
        print("SUMMARY LENGTH:", len(article.get("summary") or ""))
        print("CONTENT LENGTH:", len(article.get("content") or ""))
        print("\nCONTENT PREVIEW:\n")
        print((article.get("content") or "No RSS content available")[:1500])
        break
else:
    print("Target article was not found in the current RSS feed.")