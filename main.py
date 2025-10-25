import os, time, logging, requests, feedparser, schedule, pytz
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

# ========= CONFIG =========
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_IDS = [i.strip() for i in os.getenv("TELEGRAM_CHAT_IDS","").split(",") if i.strip()]
DATA_DIR, SENT_FILE = "data", "data/sent_links.txt"
VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")
os.makedirs(DATA_DIR, exist_ok=True)
logging.basicConfig(filename="miza_news.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# ========= TELEGRAM =========
def send(msg):
    for cid in CHAT_IDS:
        try:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                          json={"chat_id": cid, "text": msg, "parse_mode":"HTML"})
            logging.info(f"✅ Sent to {cid}")
        except Exception as e: logging.error(e)

def shorten(u):
    try:
        r=requests.get(f"https://tinyurl.com/api-create.php?url={u}",timeout=10)
        return r.text if r.status_code==200 else u
    except: return u

def sent_links():
    return set(open(SENT_FILE,encoding="utf-8").read().splitlines()) if os.path.exists(SENT_FILE) else set()

def mark_sent(l):
    open(SENT_FILE,"a",encoding="utf-8").write(l+"\n")

# ========= FEED LOGIC =========
def get_date(e):
    for k in ("published_parsed","updated_parsed"):
        if hasattr(e,k) and getattr(e,k):
            return datetime(*getattr(e,k)[:6]).astimezone(VN_TZ)
    return datetime.now(VN_TZ)

def is_recent(e):
    d=get_date(e); now=datetime.now(VN_TZ)
    return d.date()==now.date() or (now-d)<timedelta(days=1)

def summarize(e):
    title=e.get("title","Không có tiêu đề")
    link=shorten(e.get("link",""))
    src=(e.get("source",{}).get("title") or e.get("publisher") or e.get("author")
         or getattr(e,"source","Tin tổng hợp"))
    return f"📰 <b>{title}</b> ({src})\n🔗 {link}"

def check_news():
    feeds=[("Google","https://news.google.com/rss/search?q=Miza&hl=vi&gl=VN&ceid=VN:vi"),
           ("YouTube","https://rsshub.app/youtube/search/Miza"),
           ("TikTok","https://rsshub.app/tiktok/search/Miza"),
           ("Facebook","https://rsshub.app/facebook/page/mizagroup.vn"),
           ("Instagram","https://rsshub.app/instagram/tag/miza")]
    done,new=sent_links(),[]
    for name,url in feeds:
        for e in feedparser.parse(url).entries:
            l=e.get("link","")
            if l and l not in done and is_recent(e):
                e.source=name; new.append(e); mark_sent(l)
    new.sort(key=get_date,reverse=True)
    if new:
        msg="📢 <b>Tin Miza mới nhất (%s)</b>\n\n"%(datetime.now(VN_TZ).strftime("%H:%M %d/%m/%Y"))
        msg+="\n\n".join(f"{i+1}. {summarize(e)}" for i,e in enumerate(new[:15]))
        send(msg)
        logging.info(f"Sent {len(new)} posts.")
    else:
        logging.info("No new posts in 24h.")

# ========= SCHEDULE =========
def job():
    send("🌅 Xin chào! Miza AI ChatBot cập nhật tin tức hôm nay 🌞")
    check_news()

def main():
    logging.info("🚀 Miza AI ChatBot started (VN timezone mode).")
    schedule.every().day.at("09:00").do(job)
    schedule.every(10).minutes.do(check_news)
    while True:
        schedule.run_pending(); time.sleep(60)

if __name__=="__main__":
    main()
