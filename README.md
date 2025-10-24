# Miza News Bot 📰

Tự động lấy tin tức mới nhất về Công ty Cổ phần Miza (MZG) và gửi qua Telegram.

## Cấu trúc dự án
- `miza_news_bot.py` — Script chính
- `requirements.txt` — Thư viện cần cài
- `sent_links.txt` — Lưu các link đã gửi để tránh gửi trùng

## Hướng dẫn cài đặt

1. Cài thư viện:
   ```bash
   pip install -r requirements.txt
   ```

2. Sửa file `miza_news_bot.py`, thay:
   ```python
   BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
   CHAT_ID = "YOUR_CHAT_ID"
   ```

3. Chạy thử:
   ```bash
   python miza_news_bot.py
   ```

4. Bot sẽ gửi tin tức mới về Miza qua Telegram mỗi 30 phút.

