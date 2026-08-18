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

CHECK_INTERVAL = 20
DELETE_AFTER = 120
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
        else:
            print("Telegram response:", data)
    except Exception as e:
        print("Telegram error:", e)
    return False

# ================== IVASMS CLIENT ==================
class IvaSMS:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True,
                'mobile': False
            },
            delay=10
        )
        self.logged_in = False
        self.csrf = None
        self.seen = set()

    def login(self):
        print("🔐 Logging in to ivasms.com ...")
        try:
            # প্রথমে হোমপেজ
            self.scraper.get(BASE_URL, timeout=30)
            time.sleep(2)

            # লগইন পেজ
            r = self.scraper.get(f"{BASE_URL}/login", timeout=30)
            print(f"Login page status: {r.status_code}")
            print(f"Final URL: {r.url}")

            # ডিবাগ: পেজের প্রথম অংশ দেখাই
            print("Page preview (first 400 chars):")
            print(r.text[:400])
            print("-----")

            soup = BeautifulSoup(r.text, "html.parser")

            # বিভিন্ন সম্ভাব্য টোকেন খোঁজা
            token = None
            for name in ["_token", "csrf_token", "csrf", "_csrf", "token"]:
                tag = soup.find("input", {"name": name})
                if tag and tag.get("value"):
                    token = tag.get("value")
                    print(f"✅ Found token with name: {name}")
                    break

            if not token:
                # meta ট্যাগ থেকেও চেষ্টা
                meta = soup.find("meta", {"name": "csrf-token"})
                if meta:
                    token = meta.get("content")
                    print("✅ Found token from meta tag")

            if not token:
                print("❌ CSRF token still not found")
                # পুরো ফর্ম দেখাই
                forms = soup.find_all("form")
                print(f"Found {len(forms)} form(s)")
                for i, f in enumerate(forms):
                    print(f"Form {i}:", f.get("action"), f.get("method"))
                return False

            self.csrf = token

            payload = {
                "email": IVASMS_EMAIL,
                "password": IVASMS_PASSWORD,
                "_token": self.csrf
            }

            # অনেক সময় email এর বদলে username ফিল্ড থাকে
            # দুইটাই পাঠাচ্ছি
            payload["username"] = IVASMS_EMAIL

            headers = {
                "Referer": f"{BASE_URL}/login",
                "Origin": BASE_URL,
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            print("Submitting login form...")
            r2 = self.scraper.post(
                f"{BASE_URL}/login",
                data=payload,
                headers=headers,
                timeout=30,
                allow_redirects=True
            )

            print(f"After login status: {r2.status_code}")
            print(f"After login URL: {r2.url}")

            # সফল কিনা চেক
            if "/portal" in r2.url or "logout" in r2.text.lower() or "dashboard" in r2.text.lower():
                self.logged_in = True
                print("✅ Login successful!")
                return True

            # আরেকবার portal চেক
            check = self.scraper.get(f"{BASE_URL}/portal", timeout=20)
            if "logout" in check.text.lower() or "/portal" in check.url:
                self.logged_in = True
                print("✅ Login successful (second check)!")
                return True

            print("❌ Login failed")
            print("Response preview:", r2.text[:300])
            return False

        except Exception as e:
            print("Login exception:", str(e))
            return False

    def get_today_sms(self):
        if not self.logged_in:
            if not self.login():
                return []

        today = datetime.now().strftime("%Y-%m-%d")
        print(f"📥 Fetching SMS for {today} ...")

        try:
            r = self.scraper.get(f"{BASE_URL}/portal/sms/received", timeout=30)
            soup = BeautifulSoup(r.text, "html.parser")

            token_input = soup.find("input", {"name": "_token"})
            if token_input:
                self.csrf = token_input.get("value")

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
                timeout=30
            )

            soup2 = BeautifulSoup(r2.text, "html.parser")
            messages = []

            rows = soup2.select("table tbody tr") or soup2.select("tr")
            print(f"Found {len(rows)} rows")

            for row in rows:
                text_content = row.get_text(" ", strip=True)
                if len(text_content) < 15:
                    continue

                phone_match = re.search(r'\b\d{9,15}\b', text_content)
                phone = phone_match.group(0) if phone_match else "Unknown"

                msg = text_content
                uid = f"{phone}_{msg[:50]}"
                if uid in self.seen:
                    continue

                self.seen.add(uid)
                messages.append({
                    "phone": phone,
                    "msg": msg
                })

            print(f"✅ New SMS found: {len(messages)}")
            return messages

        except Exception as e:
            print("Fetch error:", e)
            self.logged_in = False
            return []

# ================== MAIN ==================
def main():
    if not all([BOT_TOKEN, CHAT_ID, IVASMS_EMAIL, IVASMS_PASSWORD]):
        print("❌ Missing environment variables!")
        return

    client = IvaSMS()
    print("🚀 IVA SMS Forwarder started...")
    print("📅 আজকের সব SMS + নতুন SMS মনিটর করা হবে")

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
                time.sleep(1.5)

            if first_run:
                print("✅ প্রথম রাউন্ড শেষ। এখন নতুন SMS মনিটর করছি...")
                first_run = False

        except Exception as e:
            print("Main error:", e)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
