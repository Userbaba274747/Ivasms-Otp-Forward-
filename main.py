import os
import time
import re
import threading
from datetime import datetime
import cloudscraper
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests

load_dotenv()

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/Global_Method_Channel1")
IVASMS_EMAIL = os.getenv("IVASMS_EMAIL")
IVASMS_PASSWORD = os.getenv("IVASMS_PASSWORD")

CHECK_INTERVAL = 15          # সেকেন্ড
DELETE_AFTER = 120           # 2 মিনিট
BASE_URL = "https://www.ivasms.com"

# ================== HELPERS ==================
def get_service(msg):
    s = (msg or "").lower()
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
    match = re.search(r'\b\d{3}[-\s]?\d{3}\b|\b\d{4,8}\b', msg or "")
    return match.group(0) if match else "OTP"

# ================== TELEGRAM ==================
def delete_message(message_id):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage",
            json={"chat_id": CHAT_ID, "message_id": message_id},
            timeout=10
        )
    except:
        pass

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
            threading.Timer(DELETE_AFTER, delete_message, args=[data["result"]["message_id"]]).start()
            print("✅ Sent to Telegram")
            return True
    except Exception as e:
        print("Telegram error:", e)
    return False

# ================== IVASMS CLIENT ==================
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
            r = self.scraper.get(f"{BASE_URL}/login", timeout=25)
            soup = BeautifulSoup(r.text, "html.parser")
            token_input = soup.find("input", {"name": "_token"})
            if not token_input:
                print("❌ CSRF token not found")
                return False

            self.csrf = token_input.get("value")

            payload = {
                "email": IVASMS_EMAIL,
                "password": IVASMS_PASSWORD,
                "_token": self.csrf
            }
            headers = {
                "Referer": f"{BASE_URL}/login",
                "Origin": BASE_URL
            }
            r2 = self.scraper.post(f"{BASE_URL}/login", data=payload, headers=headers, timeout=25)

            # Login সফল কিনা চেক
            check = self.scraper.get(f"{BASE_URL}/portal", timeout=20)
            if "logout" in check.text.lower() or "/portal" in check.url:
                self.logged_in = True
                print("✅ Login successful!")
                return True

            print("❌ Login failed. Email/Password বা Cloudflare সমস্যা হতে পারে।")
            return False

        except Exception as e:
            print("Login error:", e)
            return False

    def get_today_sms(self):
        """আজকের সব SMS আনে"""
        if not self.logged_in:
            if not self.login():
                return []

        today = datetime.now().strftime("%Y-%m-%d")
        print(f"📥 Fetching SMS for {today} ...")

        try:
            # প্রথমে received পেজে যাই
            r = self.scraper.get(f"{BASE_URL}/portal/sms/received", timeout=25)
            soup = BeautifulSoup(r.text, "html.parser")

            # CSRF আবার নিই
            token_input = soup.find("input", {"name": "_token"})
            if token_input:
                self.csrf = token_input.get("value")

            # Date দিয়ে SMS আনার চেষ্টা
            payload = {
                "from": today,
                "to": today,
                "_token": self.csrf or ""
            }
            headers = {
                "Referer": f"{BASE_URL}/portal/sms/received",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": BASE_URL
            }

            r2 = self.scraper.post(
                f"{BASE_URL}/portal/sms/received",
                data=payload,
                headers=headers,
                timeout=25
            )

            soup2 = BeautifulSoup(r2.text, "html.parser")
            messages = []

            # টেবিল থেকে ডেটা বের করা
            rows = soup2.select("table tbody tr") or soup2.select("tr")

            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 3:
                    continue

                # বিভিন্ন কলাম ট্রাই করা
                text_content = row.get_text(" ", strip=True)
                phone_match = re.search(r'\b\d{9,15}\b', text_content)
                phone = phone_match.group(0) if phone_match else "Unknown"

                # মেসেজ খোঁজা
                msg = ""
                for col in cols:
                    t = col.get_text(strip=True)
                    if len(t) > 10 and any(c.isdigit() for c in t):
                        msg = t
                        break

                if not msg:
                    msg = text_content

                if len(msg) < 8:
                    continue

                uid = f"{phone}_{msg[:40]}"
                if uid in self.seen:
                    continue

                self.seen.add(uid)
                messages.append({
                    "phone": phone,
                    "msg": msg
                })

            print(f"✅ Found {len(messages)} new SMS")
            return messages

        except Exception as e:
            print("Fetch error:", e)
            self.logged_in = False
            return []

# ================== MAIN ==================
def main():
    if not all([BOT_TOKEN, CHAT_ID, IVASMS_EMAIL, IVASMS_PASSWORD]):
        print("❌ Environment variables missing!")
        print("BOT_TOKEN, CHAT_ID, IVASMS_EMAIL, IVASMS_PASSWORD সব সেট করো")
        return

    client = IvaSMS()
    print("🚀 IVA SMS Forwarder started...")
    print("📅 আজকের সব SMS পাঠানো হবে + নতুন SMS মনিটর করা হবে")

    # প্রথমে আজকের সব SMS পাঠায়
    first_run = True

    while True:
        try:
            msgs = client.get_today_sms()

            for item in msgs:
                name, emoji = get_service(item["msg"])
                hidden = hide_phone(item["phone"])
                prefix = item["phone"][:5] if len(item["phone"]) >= 5 else item["phone"]
                otp = extract_otp(item["msg"])
                clean = item["msg"].replace("<", "&lt;").replace(">", "&gt;")

                text = (
                    f"{emoji} <b>{name}</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"📱 <b>Number:</b> <code>{hidden}</code>\n"
                    f"🔍 <b>Prefix:</b> <code>+{prefix}</code>\n"
                    f"🔑 <b>OTP:</b> <code>{otp}</code>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"<blockquote>{clean}</blockquote>\n"
                    f"⏳ <i>Auto-delete in 2 minutes</i>"
                )
                send_telegram(text, otp)
                time.sleep(1.2)  # rate limit এড়াতে

            if first_run:
                print("✅ আজকের সব SMS পাঠানো শেষ। এখন নতুন SMS মনিটর করছি...")
                first_run = False

        except Exception as e:
            print("Main loop error:", e)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
