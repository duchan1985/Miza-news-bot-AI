import os, time, requests, schedule, logging
from datetime import datetime
from dotenv import load_dotenv
from multi_source_fetcher import fetch_all_sources

# ===============================
# 🔧 Cấu hình hệ thống & Telegram
# ===============================
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SENT_FILE = "data/sent_links.txt"

# 🔨 Đảm bảo thư mục data tồn tại
os.makedirs("data", exist_ok=True)
open(SENT_FILE, "a").close()

# 🧾 Log file
logging.basicConfig(
    filename="log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ===============================
# 📤 Hàm gửi Telegram
# ===============================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})
    except Exception as e:
        logging.error(f"Telegram send error: {e}")

# ===============================
# 📚 Quản lý link đã gửi
# ===============================
def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    return set()

def save_sent(link):
    with open(SENT_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

# ===============================
# 🕵️‍♂️ Kiểm tra tin mới
# ===============================
def check_news():
    sent = load_sent()
    entries = fetch_all_sources()
    new_posts = [e for e in entries if e["link"] not in sent]

    for e in new_posts:
        msg = f"🆕 <b>{e['title']}</b>\n{e['link']}"
        send_telegram(msg)
        save_sent(e["link"])
        logging.info(f"New post: {e['title']}")

    print(f"✅ Found {len(new_posts)} new posts")
    logging.info(f"Checked news: {len(new_posts)} new posts")

# ===============================
# 🗞️ Báo cáo tổng hợp hàng ngày
# ===============================
def daily_summary():
    entries = fetch_all_sources()
    if not entries:
        send_telegram("⚠️ Không có tin mới về Miza hôm nay.")
        return

    msg = "📰 <b>Báo cáo tổng hợp tin tức Miza hôm nay</b>\n\n"
    for i, e in enumerate(entries[:10], 1):
        msg += f"{i}. <a href='{e['link']}'>{e['title']}</a>\n"
    send_telegram(msg)
    logging.info("Daily summary sent")

# ===============================
# 🕘 Lên lịch tự động
# ===============================
schedule.every().day.at("09:00").do(daily_summary)

# ===============================
# 🚀 Vòng lặp chính
# ===============================
if __name__ == "__main__":
    print("🚀 Miza Public News Bot started...")
    send_telegram("✅ Miza Analyst AI Pro+ đã khởi động.")
    while True:
        check_news()        # Kiểm tra tin mới mỗi vòng
        schedule.run_pending()
        time.sleep(1800)    # 30 phút kiểm tra 1 lần
