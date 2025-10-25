import os, time, logging, requests, feedparser, schedule, pytz
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ======================
# CONFIG
# ======================
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_IDS = [i.strip() for i in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if i.strip()]
VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")

DATA_DIR = "data"
SENT_FILE = os.path.join(DATA_DIR, "sent_links.txt")
LOG_FILE = "miza_news_realtime.log"
os.makedirs(DATA_DIR, exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s")

# ======================
# TELEGRAM
# ======================
def send_telegram(msg):
    """Gửi tin nhắn Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for chat_id in CHAT_IDS:
        try:
            requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
            logging.info(f"✅ Sent to {chat_id}")
        except Exception as e:
            logging.error(f"❌ Telegram error: {e}")

# ======================
# STORAGE
# ======================
def load_sent():
    return set(open(SENT_FILE, encoding="utf-8").read().splitlines()) if os.path.exists(SENT_FILE) else set()

def save_sent(link):
    with open(SENT_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

# ======================
# FETCH GOOGLE NEWS & YOUTUBE RSS
# ======================
def fetch_feeds(days=20):
    """Lấy dữ liệu RSS từ Google News & YouTube"""
    now = datetime.now(VN_TZ)
    cutoff = now - timedelta(days=days)

    # Nguồn tin (Google + YouTube)
    feeds = [
        # Google News
        "https://news.google.com/rss/search?q=Miza|MZG|Miza+Group|Mizagroup|Công+ty+Cổ+phần+Miza&hl=vi&gl=VN&ceid=VN:vi",
        # YouTube RSS search results (Video liên quan đến Miza)
        "https://www.youtube.com/feeds/videos.xml?playlist_id=UUd2aU53aTTxxLONczZc34BA"  # bạn có thể thay bằng playlist hoặc channel ID của Miza
    ]

    results = []
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                link = e.get("link", "")
                pub = e.get("published_parsed")
                pub_dt = datetime(*pub[:6], tzinfo=pytz.utc).astimezone(VN_TZ) if pub else now
                if pub_dt < cutoff:
                    continue
                title = e.get("title", "Không có tiêu đề")
                source = e.get("source", {}).get("title", "")
                results.append({
                    "title": title,
                    "link": link,
                    "date": pub_dt,
                    "source": source
                })
        except Exception as e:
            logging.error(f"RSS parse error for {url}: {e}")

    # Sắp xếp mới nhất
    results.sort(key=lambda x: x["date"], reverse=True)
    return results

# ======================
# SHORTEN URL
# ======================
def shorten_url(url):
    try:
        res = requests.get(f"https://tinyurl.com/api-create.php?url={url}", timeout=5)
        return res.text if res.status_code == 200 else url
    except:
        return url

# ======================
# FORMAT MESSAGE
# ======================
def format_message(news_list):
    lines = []
    for i, n in enumerate(news_list, 1):
        short = shorten_url(n["link"])
        src = f" - {n['source']}" if n["source"] else ""
        lines.append(f"{i}. <b>{n['title']}</b>{src}\n🔗 {short}")
    return "\n\n".join(lines)

# ======================
# DAILY SUMMARY JOB (9h sáng)
# ======================
def job_daily_summary():
    news = fetch_feeds(days=20)
    if not news:
        send_telegram("⚠️ Không có tin mới về Miza trong 20 ngày qua.")
        return

    now = datetime.now(VN_TZ)
    header = f"📢 <b>Tổng hợp tin Miza (20 ngày gần nhất) - {now.strftime('%H:%M %d/%m')}</b>\n\n"
    body = format_message(news[:20])
    send_telegram(header + body)
    logging.info("✅ Sent daily summary.")
    print(f"✅ Sent {len(news[:20])} news to Telegram.")

# ======================
# REAL-TIME MONITORING (5 phút)
# ======================
def job_realtime_check():
    sent = load_sent()
    new_items = []
    for item in fetch_feeds(days=20):
        if item["link"] not in sent:
            new_items.append(item)
            save_sent(item["link"])

    if new_items:
        now = datetime.now(VN_TZ)
        header = f"🆕 <b>Tin Miza mới phát sinh ({now.strftime('%H:%M %d/%m')})</b>\n\n"
        body = format_message(new_items[:5])
        send_telegram(header + body)
        print(f"🚨 Gửi ngay {len(new_items)} tin mới phát hiện.")
        logging.info(f"🚨 Sent {len(new_items)} new items.")
    else:
        print("⏳ Không có tin mới (check 5 phút).")

# ======================
# MAIN LOOP
# ======================
def main():
    logging.info("🚀 Miza News Bot (Realtime 20 days) started.")
    send_telegram("🚀 Miza News Bot (Realtime) khởi động thành công.")

    # Gửi bản tổng hợp 9h sáng mỗi ngày
    schedule.every().day.at("09:00").do(job_daily_summary)

    # Kiểm tra tin mới mỗi 5 phút
    schedule.every(5).minutes.do(job_realtime_check)

    # Chạy ngay khi khởi động
    job_realtime_check()

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
