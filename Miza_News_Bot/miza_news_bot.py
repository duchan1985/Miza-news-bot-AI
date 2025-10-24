import requests
import feedparser
import time
import os

# =========================
# CẤU HÌNH
# =========================
BOT_TOKEN = "8466574154:AAFVs6xvbmyLUx1joSr4L4wA1JLRcumnBZM"  # 👉 thay bằng token thật
CHAT_ID = "5932319683"              # 👉 thay bằng ID người nhận
RSS_URL = "https://news.google.com/rss/search?q=(Công+ty+Cổ+phần+Miza)+OR+(Miza+Joint+Stock+Company)+OR+(MZG)&hl=vi&gl=VN&ceid=VN:vi"
CHECK_INTERVAL = 1800  # 30 phút kiểm tra 1 lần 
SENT_FILE = "sent_links.txt"

# =========================
# HÀM HỖ TRỢ
# =========================

def load_sent_links():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    return set()

def save_sent_link(link):
    with open(SENT_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload)
        if r.status_code != 200:
            print("❌ Gửi tin thất bại:", r.text)
    except Exception as e:
        print("⚠️ Lỗi gửi Telegram:", e)

def check_news():
    print("🔍 Đang kiểm tra tin tức Miza...")
    sent_links = load_sent_links()
    feed = feedparser.parse(RSS_URL)
    new_count = 0

    for entry in feed.entries[:10]:  # chỉ lấy 10 bài mới nhất
        title = entry.title
        link = entry.link
        published = entry.published if hasattr(entry, "published") else ""

        if link not in sent_links:
            message = f"📰 <b>{title}</b>\n{published}\n🔗 {link}"
            send_telegram_message(message)
            save_sent_link(link)
            new_count += 1
            time.sleep(2)  # tránh spam Telegram

    print(f"✅ Đã gửi {new_count} bài mới.")

# =========================
# CHẠY LIÊN TỤC
# =========================

if __name__ == "__main__":
    while True:
        check_news()
        print(f"⏳ Chờ {CHECK_INTERVAL/60} phút...")
        time.sleep(CHECK_INTERVAL)
