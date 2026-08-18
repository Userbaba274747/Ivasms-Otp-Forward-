import os
import time
import re
import json
import cloudscraper
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests

load_dotenv()

# ========== CONFIG ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/Global_Method_Channel1")
IVASMS_EMAIL = os.getenv("IVASMS_EMAIL")
IVASMS_PASSWORD = os.getenv("IVASMS_PASSWORD")

CHECK_INTERVAL = 12          # সেকেন্ড
DELETE_AFTER = 120           # 2 মিনিট
BASE_URL = "https://www.ivasms.com"

# ========== HELPERS ==========
def get_service(msg):
    s = msg.lower()
    if "telegram" in s: return "Telegram", "✈️"
    if "facebook" in s: return "Facebook", "📘"
    if "google" in s: return "Google", "🌐"
    if "imo" in s: return "Imo", "🔵"
    if "tiktok" in s: return "TikTok", "🎵"
    if "whatsapp business" in s: return "WhatsApp Business", "💬"
    return "WhatsApp", "💬"

def hide_phone(phone):
    if not phone or len(phone) < 8:
        return phone
    return phone[:5] + "****" + phone[-3:]

def extract_otp(msg):
    match = re.search(r'\b\d{3}[-\s]?\d{3}\b|\b\d{4,8}\b', msg)
    return match.group(0) if match else "OTP"

# ========== TELEGRAM ==========
def delete_message(message_id):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage",
            json={"chat_id": CHAT_ID, "message_id": message_id},
            timeout=10
        )
    except Exception as e:
        print("Delete error:", e)

def send_telegram(text, otp):
    try:
        res = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
                "reply_markup": {
                    "inline_keyboard": [[
                        {"text": "📋 Copy OTP", "copy_text": {"text": otp}},
                        {"text": "📢 Join Channel", "url": CHANNEL_LINK}
                    ]]
                }
            },
            timeout=15
        )
        data = res.json()
        if data.get("ok") and data["result"].get("message_id"):
            # 2 মিনিট পর ডিলিট
            time.sleep(0.5)
            # setTimeout এর বদলে background এ রাখার জন্য আলাদা থ্রেড ব্যবহার করা ভালো, 
            # কিন্তু সহজ রাখার জন্য এখানে simple delay দিলাম না। 
            # চাইলে পরে threading যোগ করা যাবে।
            import threading
            threading.Timer(DELETE_AFTER, delete_message, args=[data["result"]["message_id"]]).start()
            print("✅ Message sent & scheduled for delete")
    except Exception as e:
        print("Telegram send error:", e)

# ========== IVASMS CLIENT ==========
class IvaSMS:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
        )
        self.logged_in = False
        self.csrf = None
        self.seen = set()

    def login(self):
        print("🔐 Logging in to ivasms.com ...")
        try:
            # Step 1: Get login page
            r = self.scraper.get(f"{BASE_URL}/login", timeout=20)
            soup = BeautifulSoup(r.text, "lxml")
            token = soup.find("input", {"name": "_token"})
            if not token:
                print("❌ CSRF token not found on login page")
                return False

            self.csrf = token.get("value")

            # Step 2: Submit login
            payload = {
                "email": IVASMS_EMAIL,
                "password": IVASMS_PASSWORD,
                "_token": self.csrf
            }
            headers = {
                "Referer": f"{BASE_URL}/login",
                "Origin": BASE_URL
            }
            r2 = self.scraper.post(f"{BASE_URL}/login", data=payload, headers=headers, timeout=20)

            if "portal" in r2.url or r2.status_code == 200:
                # Check if really logged in
                check = self.scraper.get(f"{BASE_URL}/portal/live/my_sms", timeout=15)
                if "logout" in check.text.lower() or "my_sms" in check.url:
                    self.logged_in = True
                    print("✅ Login successful!")
                    return True

            print("❌ Login failed. Check email/password or Cloudflare blocked.")
            return False

        except Exception as e:
            print("Login error:", e)
            return False

    def get_live_sms(self):
        if not self.logged_in:
            if not self.login():
                return []

        try:
            r = self.scraper.get(f"{BASE_URL}/portal/live/my_sms", timeout=20)
            soup = BeautifulSoup(r.text, "lxml")

            messages = []
            rows = soup.select("table tbody tr") or soup.select("tr")

            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 5:
                    continue

                live = cols[0].get_text(strip=True)
                sid = cols[1].get_text(strip=True)
                msg = cols[4].get_text(strip=True)

                if not msg or len(msg) < 5:
                    continue

                uid = f"{live}_{msg}"
                if uid in self.seen:
                    continue

                self.seen.add(uid)
                if len(self.seen) > 200:
                    self.seen = set(list(self.seen)[-100:])

                phone_match = re.search(r'\d{8,15}', live)
                phone = phone_match.group(0) if phone_match else live

                messages.append({
                    "phone": phone,
                    "service_raw": sid,
                    "msg": msg
                })

            return messages

        except Exception as e:
            print("Fetch SMS error:", e)
            self.logged_in = False
            return []

# ========== MAIN LOOP ==========
def main():
    if not all([BOT_TOKEN, CHAT_ID, IVASMS_EMAIL, IVASMS_PASSWORD]):
        print("❌ Missing environment variables!")
        return

    client = IvaSMS()
    print("🚀 IVA SMS Forwarder started on Railway...")

    while True:
        try:
            msgs = client.get_live_sms()
            for item in msgs:
                name, emoji = get_service(item["msg"])
                hidden = hide_phone(item["phone"])
                prefix = item["phone"][:5] if len(item["phone"]) >= 5 else item["phone"]
                otp = extract_otp(item["msg"])
                clean_msg = item["msg"].replace("<", "&lt;").replace(">", "&gt;")

                text = (
                    f"{emoji} <b>{name}</b> 🌐\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"📱 <b>Number:</b> <code>{hidden}</code>\n"
                    f"🔍 <b>Prefix:</b> <code>+{prefix}</code>\n"
                    f"🔑 <b>OTP:</b> <code>{otp}</code>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"<blockquote>{clean_msg}</blockquote>\n"
                    f"⏳ <i>This message will auto-delete in 2 minutes</i>"
                )
                send_telegram(text, otp)

        except Exception as e:
            print("Main loop error:", e)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
