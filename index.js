require('dotenv').config();
const fetch = require('node-fetch');

const BOT_TOKEN = process.env.BOT_TOKEN;
const CHAT_ID = process.env.CHAT_ID;
const CHANNEL_LINK = process.env.CHANNEL_LINK || "https://t.me/Global_Method_Channel1";
const CHECK_INTERVAL = 15000; // 15 সেকেন্ড পর পর চেক করবে
const DELETE_AFTER = 120000;  // 2 মিনিট

// এখানে তোমার ivasms থেকে পাওয়া ডেটা আসবে (পরে রিয়েল স্ক্র্যাপিং যোগ করা যাবে)
let lastSeen = new Set();

function getServiceDetails(msg) {
  const s = msg.toLowerCase();
  if (s.includes('telegram')) return { name: 'Telegram', emoji: '✈️' };
  if (s.includes('facebook')) return { name: 'Facebook', emoji: '📘' };
  if (s.includes('google')) return { name: 'Google', emoji: '🌐' };
  if (s.includes('imo')) return { name: 'Imo', emoji: '🔵' };
  if (s.includes('tiktok')) return { name: 'TikTok', emoji: '🎵' };
  return { name: 'WhatsApp', emoji: '💬' };
}

function hidePhone(phone) {
  if (!phone || phone.length < 8) return phone;
  return phone.slice(0, 5) + "****" + phone.slice(-3);
}

async function deleteMessage(messageId) {
  try {
    await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/deleteMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: CHAT_ID,
        message_id: messageId
      })
    });
  } catch (e) {
    console.log("Delete error:", e.message);
  }
}

async function sendToTelegram(text, otp) {
  try {
    const res = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: CHAT_ID,
        text: text,
        parse_mode: "HTML",
        disable_web_page_preview: true,
        reply_markup: {
          inline_keyboard: [
            [
              { text: "📋 Copy OTP", copy_text: { text: otp } },
              { text: "📢 Join Channel", url: CHANNEL_LINK }
            ]
          ]
        }
      })
    });

    const data = await res.json();
    if (data.ok && data.result?.message_id) {
      setTimeout(() => deleteMessage(data.result.message_id), DELETE_AFTER);
    }
  } catch (e) {
    console.log("Send error:", e.message);
  }
}

// ========== এখানে রিয়েল ivasms স্ক্র্যাপিং যোগ করতে হবে ==========
// বর্তমানে ডেমো হিসেবে কাজ করছে। 
// রিয়েল ভার্সনের জন্য cookies + cloudscraper বা puppeteer লাগবে।
async function checkNewSms() {
  console.log("Checking for new SMS... (demo mode)");

  // ডেমো ডেটা (টেস্টিং এর জন্য)
  // রিয়েল প্রজেক্টে এখানে ivasms পেজ থেকে ডেটা আনতে হবে
  const demoMessages = [];

  for (const item of demoMessages) {
    const uid = item.phone + "_" + item.msg;
    if (lastSeen.has(uid)) continue;
    lastSeen.add(uid);

    const service = getServiceDetails(item.msg);
    const hidden = hidePhone(item.phone);
    const prefix = item.phone.slice(0, 5);
    const otpMatch = item.msg.match(/\b\d{3}[-\s]?\d{3}\b|\b\d{4,8}\b/);
    const otp = otpMatch ? otpMatch[0] : "OTP";

    const text = `\( {service.emoji} <b> \){service.name}</b> 🌐\n` +
                 `━━━━━━━━━━━━━━━━━━━━\n` +
                 `📱 <b>Number:</b> <code>${hidden}</code>\n` +
                 `🔍 <b>Prefix:</b> <code>+${prefix}</code>\n` +
                 `🔑 <b>OTP:</b> <code>${otp}</code>\n` +
                 `━━━━━━━━━━━━━━━━━━━━\n` +
                 `<blockquote>${item.msg}</blockquote>\n` +
                 `⏳ <i>This message will auto-delete in 2 minutes</i>`;

    await sendToTelegram(text, otp);
  }
}

console.log("🚀 IVA SMS Forwarder started on Railway...");
setInterval(checkNewSms, CHECK_INTERVAL);
checkNewSms();
