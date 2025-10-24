import os
import time
import logging
import requests
import feedparser
import schedule
from datetime import datetime
from urllib.parse import quote
from dotenv import load_dotenv

# ======================
# CONFIG & SETUP
# ======================
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh")

DATA_DIR = "data"
SENT_FILE = os.path.join(DATA_DIR, "sent_links.txt")
LOG_FILE = "miza_news.log"

os.makedirs(DATA_DIR, exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ======================
# CORE FUNCTIONS
# ======================

def send_telegram(msg):
    """Gửi tin nhắn đến Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        logging.error(f"Telegram error: {e}")

def shorten_url(url):
    """Rút gọn link"""
    try:
        res = requests.get(f"https://tinyurl.com/api-create.php?url={url}", timeout=10)
        return res.text if res.status_code == 200 else url
    except:
        return url

def load_sent():
    """Đọc danh sách link đã gửi"""
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    return set()

def save_sent(link):
    """Lưu link đã gửi để tránh gửi lại"""
    with open(SENT_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

def fetch_feed(url):
    """Lấy tin RSS"""
    try:
        feed = feedparser.parse(url)
        return feed.entries
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
        return []

def summarize_entry(entry):
    """Tạo nội dung ngắn gọn & gọn gàng"""
    title = entry.get("title", "Không có tiêu đề")
    link = shorten_url(entry.get("link", ""))
    source = entry.get("source", {}).get("title", "") or entry.get("publisher", "") or ""
    return f"📰 <b>{title}</b> {('- ' + source) if source else ''}\n🔗 {link}"

# ======================
# NEWS CHECKER
# ======================

def check_news():
    logging.info("Fetching latest Miza news ...")
    sent = load_sent()
    new_posts = []

    feeds = [
        # Google News
        f"https://news.google.com/rss/search?q=Miza&hl=vi&gl=VN&ceid=VN:vi",
        # RSSHub fallback
        f"https://rsshub.app/youtube/search/Miza",
        f"https://rsshub.app/tiktok/search/Miza",
        f"https://rsshub.app/facebook/page/mizagroup.vn",
        f"https://rsshub.app/instagram/tag/miza"
    ]

    for url in feeds:
        entries = fetch_feed(url)
        for e in entries:
            link = e.get("link", "")
            if link and link not in sent:
                msg = summarize_entry(e)
                new_posts.append(msg)
                save_sent(link)

    if new_posts:
        msg_header = f"📢 <b>Cập nhật mới về Miza ({datetime.now().strftime('%H:%M %d/%m')})</b>\n\n"
        formatted = "\n\n".join(f"{i+1}. {p}" for i, p in enumerate(new_posts[:10]))
        send_telegram(msg_header + formatted)
        logging.info(f"Sent {len(new_posts)} new posts.")
    else:
        logging.info("No new posts found.")

# ======================
# SCHEDULE JOBS
# ======================

def job_daily():
    now = datetime.now().strftime("%H:%M")
    if now == "09:00":
        send_telegram("🤖 Xin chào! Miza AI ChatBot sẵn sàng cập nhật tin tức hôm nay 🌅")
    check_news()

def main():
    logging.info("Miza AI News Bot started successfully (quiet mode).")

    # Lịch gửi tin và kiểm tra định kỳ
    schedule.every().day.at("09:00").do(job_daily)
    schedule.every(10).minutes.do(check_news)

    while True:
        schedule.run_pending()
        time.sleep(60)

# ======================
# RUN
# ======================
if __name__ == "__main__":
    main()
