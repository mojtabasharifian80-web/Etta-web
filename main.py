import requests
from bs4 import BeautifulSoup
import os
import time

CHANNEL = os.getenv("EITAA_CHANNEL")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_IDS = [cid.strip() for cid in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if cid.strip()]
LIMIT = 10

def get_latest_messages(channel):
    url = f"https://eitaa.com/{channel}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        messages = []
        posts = soup.find_all("div", class_="etme_widget_message")
        
        for post in posts[:LIMIT]:
            text_div = post.find("div", class_="etme_widget_message_text")
            text = text_div.get_text(separator="\n", strip=True) if text_div else ""
            
            post_url = ""
            link_tag = post.find("a", href=True)
            if link_tag and channel in link_tag.get("href", ""):
                href = link_tag["href"]
                if href.startswith("/"):
                    post_url = "https://eitaa.com" + href
                else:
                    post_url = href
            
            if text.strip():
                full_msg = f"{text}\n\n🔗 {post_url}" if post_url else text
                messages.append(full_msg)
        
        return messages
    except Exception as e:
        return [f"❌ خطا در دریافت پیام‌ها:\n{str(e)}"]

def send_to_telegram(text, chat_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text[:4090],
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, data=data, timeout=30)
        return response.status_code == 200
    except Exception as e:
        print(f"خطا در ارسال به {chat_id}: {e}")
        return False

if __name__ == "__main__":
    if not all([CHANNEL, TOKEN]) or not CHAT_IDS:
        print("خطا: متغیرهای محیطی تنظیم نشده‌اند")
        exit(1)
    
    print(f"در حال دریافت پیام‌های کانال {CHANNEL}...")
    print(f"تعداد اکانت‌ها: {len(CHAT_IDS)}")
    msgs = get_latest_messages(CHANNEL)
    
    if not msgs:
        for chat_id in CHAT_IDS:
            send_to_telegram("هیچ پیامی پیدا نشد.", chat_id)
    else:
        for i, msg in enumerate(reversed(msgs), 1):
            for chat_id in CHAT_IDS:
                success = send_to_telegram(msg, chat_id)
                print(f"پیام {i} به {chat_id} ارسال شد: {success}")
            time.sleep(1.2)
    
    print(f"تمام. تعداد پیام‌ها: {len(msgs)}")
