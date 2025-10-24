import feedparser, time

# Cấu hình các nguồn tin công khai qua RSSHub hoặc Google News
SOURCES = [
    {"name": "Google News", "url": "https://news.google.com/rss/search?q=Miza&hl=vi&gl=VN&ceid=VN:vi"},
    {"name": "YouTube", "url": "https://rsshub.app/youtube/search/Miza"},
    {"name": "TikTok", "url": "https://rsshub.app/tiktok/search/Miza"},
    {"name": "Facebook", "url": "https://rsshub.app/facebook/page/MizaPaper"},
    {"name": "Instagram", "url": "https://rsshub.app/instagram/user/miza.vn"},
]

def parse_rss(url):
    """Đọc và lọc các bài có chữ 'Miza' trong tiêu đề."""
    feed = feedparser.parse(url)
    results = []
    for e in feed.entries[:10]:
        title, link = e.get("title", ""), e.get("link", "")
        if "miza" in title.lower():
            results.append({"title": title.strip(), "link": link.strip()})
    return results

def fetch_all_sources():
    """Lấy tin từ tất cả nguồn."""
    all_entries = []
    for s in SOURCES:
        print(f"🔍 Fetching from {s['name']} ...")
        try:
            items = parse_rss(s["url"])
            all_entries.extend(items)
        except Exception as e:
            print(f"⚠️ Error fetching {s['name']}: {e}")
        time.sleep(1)
    return all_entries
