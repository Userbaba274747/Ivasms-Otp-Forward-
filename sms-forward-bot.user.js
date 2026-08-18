// ==UserScript==
// @name         IVA SMS Telegram Custom Format (Beautiful + Auto Delete)
// @namespace    http://tampermonkey.net/
// @version      17.0
// @match        https://www.ivasms.com/portal/*
// @match        https://www.ivasms.com/portal/live/my_sms*
// @match        https://*.ivasms.com/*
// @grant        none
// @run-at       document-end
// ==/UserScript==

(function() {
    'use strict';

    const BOT_TOKEN = "8564093311:AAE1wtnRDybV4oOH3HgmJbHplsBovYVtZm8";
    const CHAT_ID = "-1003178872820";
    const CHANNEL_LINK = "https://t.me/Global_Method_Channel1";
    const CHECK_INTERVAL = 500;
    const DELETE_AFTER = 120000; // 2 minutes

    let sentSmsIds = JSON.parse(localStorage.getItem('sent_sms_ids_v17') || '[]');

    function getCountryInfo(liveText) {
        let textUpper = liveText.toUpperCase();
        let phoneDigits = liveText.replace(/\D/g, '');

        if (textUpper.includes('AFGHANISTAN')) return { flag: '🇦🇫', code: 'AF' };
        if (textUpper.includes('ALBANIA')) return { flag: '🇦🇱', code: 'AL' };
        if (textUpper.includes('ALGERIA')) return { flag: '🇩🇿', code: 'DZ' };
        if (textUpper.includes('ARGENTINA')) return { flag: '🇦🇷', code: 'AR' };
        if (textUpper.includes('BANGLADESH')) return { flag: '🇧🇩', code: 'BD' };
        if (textUpper.includes('BRAZIL')) return { flag: '🇧🇷', code: 'BR' };
        if (textUpper.includes('CANADA')) return { flag: '🇨🇦', code: 'CA' };
        if (textUpper.includes('CHINA')) return { flag: '🇨🇳', code: 'CN' };
        if (textUpper.includes('EGYPT')) return { flag: '🇪🇬', code: 'EG' };
        if (textUpper.includes('FRANCE')) return { flag: '🇫🇷', code: 'FR' };
        if (textUpper.includes('GERMANY')) return { flag: '🇩🇪', code: 'DE' };
        if (textUpper.includes('INDIA')) return { flag: '🇮🇳', code: 'IN' };
        if (textUpper.includes('INDONESIA')) return { flag: '🇮🇩', code: 'ID' };
        if (textUpper.includes('IRAQ')) return { flag: '🇮🇶', code: 'IQ' };
        if (textUpper.includes('ITALY')) return { flag: '🇮🇹', code: 'IT' };
        if (textUpper.includes('JAPAN')) return { flag: '🇯🇵', code: 'JP' };
        if (textUpper.includes('MALAYSIA')) return { flag: '🇲🇾', code: 'MY' };
        if (textUpper.includes('MEXICO')) return { flag: '🇲🇽', code: 'MX' };
        if (textUpper.includes('NIGERIA')) return { flag: '🇳🇬', code: 'NG' };
        if (textUpper.includes('PAKISTAN')) return { flag: '🇵🇰', code: 'PK' };
        if (textUpper.includes('PHILIPPINES')) return { flag: '🇵🇭', code: 'PH' };
        if (textUpper.includes('RUSSIA')) return { flag: '🇷🇺', code: 'RU' };
        if (textUpper.includes('SAUDI')) return { flag: '🇸🇦', code: 'SA' };
        if (textUpper.includes('TURKEY')) return { flag: '🇹🇷', code: 'TR' };
        if (textUpper.includes('UAE') || textUpper.includes('EMIRATES')) return { flag: '🇦🇪', code: 'AE' };
        if (textUpper.includes('UK') || textUpper.includes('UNITED KINGDOM')) return { flag: '🇬🇧', code: 'GB' };
        if (textUpper.includes('USA') || textUpper.includes('UNITED STATES')) return { flag: '🇺🇸', code: 'US' };

        if (phoneDigits.startsWith('1809') || phoneDigits.startsWith('1829')) return { flag: '🇩🇴', code: 'DO' };
        if (phoneDigits.startsWith('1876')) return { flag: '🇯🇲', code: 'JM' };
        if (phoneDigits.startsWith('966')) return { flag: '🇸🇦', code: 'SA' };
        if (phoneDigits.startsWith('880')) return { flag: '🇧🇩', code: 'BD' };
        if (phoneDigits.startsWith('971')) return { flag: '🇦🇪', code: 'AE' };
        if (phoneDigits.startsWith('973')) return { flag: '🇧🇭', code: 'BH' };
        if (phoneDigits.startsWith('974')) return { flag: '🇶🇦', code: 'QA' };
        if (phoneDigits.startsWith('965')) return { flag: '🇰🇼', code: 'KW' };
        if (phoneDigits.startsWith('968')) return { flag: '🇴🇲', code: 'OM' };
        if (phoneDigits.startsWith('962')) return { flag: '🇯🇴', code: 'JO' };
        if (phoneDigits.startsWith('964')) return { flag: '🇮🇶', code: 'IQ' };
        if (phoneDigits.startsWith('963')) return { flag: '🇸🇾', code: 'SY' };
        if (phoneDigits.startsWith('967')) return { flag: '🇾🇪', code: 'YE' };
        if (phoneDigits.startsWith('970')) return { flag: '🇵🇸', code: 'PS' };
        if (phoneDigits.startsWith('972')) return { flag: '🇮🇱', code: 'IL' };
        if (phoneDigits.startsWith('977')) return { flag: '🇳🇵', code: 'NP' };
        if (phoneDigits.startsWith('855')) return { flag: '🇰🇭', code: 'KH' };
        if (phoneDigits.startsWith('852')) return { flag: '🇭🇰', code: 'HK' };
        if (phoneDigits.startsWith('886')) return { flag: '🇹🇼', code: 'TW' };
        if (phoneDigits.startsWith('223')) return { flag: '🇲🇱', code: 'ML' };
        if (phoneDigits.startsWith('234')) return { flag: '🇳🇬', code: 'NG' };
        if (phoneDigits.startsWith('254')) return { flag: '🇰🇪', code: 'KE' };
        if (phoneDigits.startsWith('212')) return { flag: '🇲🇦', code: 'MA' };
        if (phoneDigits.startsWith('213')) return { flag: '🇩🇿', code: 'DZ' };
        if (phoneDigits.startsWith('216')) return { flag: '🇹🇳', code: 'TN' };
        if (phoneDigits.startsWith('218')) return { flag: '🇱🇾', code: 'LY' };
        if (phoneDigits.startsWith('244')) return { flag: '🇦🇴', code: 'AO' };
        if (phoneDigits.startsWith('225')) return { flag: '🇨🇮', code: 'CI' };
        if (phoneDigits.startsWith('237')) return { flag: '🇨🇲', code: 'CM' };
        if (phoneDigits.startsWith('251')) return { flag: '🇪🇹', code: 'ET' };
        if (phoneDigits.startsWith('233')) return { flag: '🇬🇭', code: 'GH' };
        if (phoneDigits.startsWith('258')) return { flag: '🇲🇿', code: 'MZ' };
        if (phoneDigits.startsWith('255')) return { flag: '🇹🇿', code: 'TZ' };
        if (phoneDigits.startsWith('256')) return { flag: '🇺🇬', code: 'UG' };
        if (phoneDigits.startsWith('260')) return { flag: '🇿🇲', code: 'ZM' };
        if (phoneDigits.startsWith('263')) return { flag: '🇿🇼', code: 'ZW' };
        if (phoneDigits.startsWith('355')) return { flag: '🇦🇱', code: 'AL' };
        if (phoneDigits.startsWith('374')) return { flag: '🇦🇲', code: 'AM' };
        if (phoneDigits.startsWith('375')) return { flag: '🇧🇾', code: 'BY' };
        if (phoneDigits.startsWith('380')) return { flag: '🇺🇦', code: 'UA' };
        if (phoneDigits.startsWith('381')) return { flag: '🇷🇸', code: 'RS' };
        if (phoneDigits.startsWith('385')) return { flag: '🇭🇷', code: 'HR' };
        if (phoneDigits.startsWith('387')) return { flag: '🇧🇦', code: 'BA' };
        if (phoneDigits.startsWith('359')) return { flag: '🇧🇬', code: 'BG' };
        if (phoneDigits.startsWith('420')) return { flag: '🇨🇿', code: 'CZ' };
        if (phoneDigits.startsWith('357')) return { flag: '🇨🇾', code: 'CY' };
        if (phoneDigits.startsWith('358')) return { flag: '🇫🇮', code: 'FI' };
        if (phoneDigits.startsWith('992')) return { flag: '🇹🇯', code: 'TJ' };
        if (phoneDigits.startsWith('994')) return { flag: '🇦🇿', code: 'AZ' };
        if (phoneDigits.startsWith('995')) return { flag: '🇬🇪', code: 'GE' };
        if (phoneDigits.startsWith('996')) return { flag: '🇰🇬', code: 'KG' };
        if (phoneDigits.startsWith('998')) return { flag: '🇺🇿', code: 'UZ' };
        if (phoneDigits.startsWith('91')) return { flag: '🇮🇳', code: 'IN' };
        if (phoneDigits.startsWith('92')) return { flag: '🇵🇰', code: 'PK' };
        if (phoneDigits.startsWith('90')) return { flag: '🇹🇷', code: 'TR' };
        if (phoneDigits.startsWith('93')) return { flag: '🇦🇫', code: 'AF' };
        if (phoneDigits.startsWith('94')) return { flag: '🇱🇰', code: 'LK' };
        if (phoneDigits.startsWith('95')) return { flag: '🇲🇲', code: 'MM' };
        if (phoneDigits.startsWith('98')) return { flag: '🇮🇷', code: 'IR' };
        if (phoneDigits.startsWith('60')) return { flag: '🇲🇾', code: 'MY' };
        if (phoneDigits.startsWith('62')) return { flag: '🇮🇩', code: 'ID' };
        if (phoneDigits.startsWith('63')) return { flag: '🇵🇭', code: 'PH' };
        if (phoneDigits.startsWith('64')) return { flag: '🇳🇿', code: 'NZ' };
        if (phoneDigits.startsWith('65')) return { flag: '🇸🇬', code: 'SG' };
        if (phoneDigits.startsWith('66')) return { flag: '🇹🇭', code: 'TH' };
        if (phoneDigits.startsWith('81')) return { flag: '🇯🇵', code: 'JP' };
        if (phoneDigits.startsWith('82')) return { flag: '🇰🇷', code: 'KR' };
        if (phoneDigits.startsWith('84')) return { flag: '🇻🇳', code: 'VN' };
        if (phoneDigits.startsWith('86')) return { flag: '🇨🇳', code: 'CN' };
        if (phoneDigits.startsWith('51')) return { flag: '🇵🇪', code: 'PE' };
        if (phoneDigits.startsWith('52')) return { flag: '🇲🇽', code: 'MX' };
        if (phoneDigits.startsWith('53')) return { flag: '🇨🇺', code: 'CU' };
        if (phoneDigits.startsWith('54')) return { flag: '🇦🇷', code: 'AR' };
        if (phoneDigits.startsWith('55')) return { flag: '🇧🇷', code: 'BR' };
        if (phoneDigits.startsWith('56')) return { flag: '🇨🇱', code: 'CL' };
        if (phoneDigits.startsWith('57')) return { flag: '🇨🇴', code: 'CO' };
        if (phoneDigits.startsWith('58')) return { flag: '🇻🇪', code: 'VE' };
        if (phoneDigits.startsWith('591')) return { flag: '🇧🇴', code: 'BO' };
        if (phoneDigits.startsWith('593')) return { flag: '🇪🇨', code: 'EC' };
        if (phoneDigits.startsWith('595')) return { flag: '🇵🇾', code: 'PY' };
        if (phoneDigits.startsWith('598')) return { flag: '🇺🇾', code: 'UY' };
        if (phoneDigits.startsWith('20')) return { flag: '🇪🇬', code: 'EG' };
        if (phoneDigits.startsWith('27')) return { flag: '🇿🇦', code: 'ZA' };
        if (phoneDigits.startsWith('30')) return { flag: '🇬🇷', code: 'GR' };
        if (phoneDigits.startsWith('31')) return { flag: '🇳🇱', code: 'NL' };
        if (phoneDigits.startsWith('32')) return { flag: '🇧🇪', code: 'BE' };
        if (phoneDigits.startsWith('33')) return { flag: '🇫🇷', code: 'FR' };
        if (phoneDigits.startsWith('34')) return { flag: '🇪🇸', code: 'ES' };
        if (phoneDigits.startsWith('36')) return { flag: '🇭🇺', code: 'HU' };
        if (phoneDigits.startsWith('39')) return { flag: '🇮🇹', code: 'IT' };
        if (phoneDigits.startsWith('40')) return { flag: '🇷🇴', code: 'RO' };
        if (phoneDigits.startsWith('41')) return { flag: '🇨🇭', code: 'CH' };
        if (phoneDigits.startsWith('43')) return { flag: '🇦🇹', code: 'AT' };
        if (phoneDigits.startsWith('44')) return { flag: '🇬🇧', code: 'GB' };
        if (phoneDigits.startsWith('45')) return { flag: '🇩🇰', code: 'DK' };
        if (phoneDigits.startsWith('46')) return { flag: '🇸🇪', code: 'SE' };
        if (phoneDigits.startsWith('47')) return { flag: '🇳🇴', code: 'NO' };
        if (phoneDigits.startsWith('48')) return { flag: '🇵🇱', code: 'PL' };
        if (phoneDigits.startsWith('49')) return { flag: '🇩🇪', code: 'DE' };
        if (phoneDigits.startsWith('77')) return { flag: '🇰🇿', code: 'KZ' };
        if (phoneDigits.startsWith('7')) return { flag: '🇷🇺', code: 'RU' };
        if (phoneDigits.startsWith('1')) return { flag: '🇺🇸', code: 'US' };

        return { flag: '🌐', code: 'unknow' };
    }

    function getServiceDetails(serviceRaw, msg) {
        let s = (serviceRaw + " " + msg).toLowerCase();
        if (s.includes('telegram')) return { name: 'Telegram', emoji: '✈️' };
        if (s.includes('facebook')) return { name: 'Facebook', emoji: '📘' };
        if (s.includes('google')) return { name: 'Google', emoji: '🌐' };
        if (s.includes('imo')) return { name: 'Imo', emoji: '🔵' };
        if (s.includes('tiktok')) return { name: 'TikTok', emoji: '🎵' };
        if (s.includes('whatsapp business')) return { name: 'WhatsApp Business', emoji: '💬' };
        return { name: 'WhatsApp', emoji: '💬' };
    }

    function hidePhoneNumber(phone) {
        if (!phone || phone.length < 8) return phone;
        let prefix = phone.slice(0, 5);
        let suffix = phone.slice(-3);
        return prefix + "****" + suffix;
    }

    function deleteMessage(messageId) {
        fetch(`https://api.telegram.org/bot${BOT_TOKEN}/deleteMessage`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                chat_id: CHAT_ID,
                message_id: messageId
            })
        }).catch(e => console.log("Delete Error:", e));
    }

    function sendToTelegram(text, otp, emoji) {
        fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
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
                            {
                                text: "📋 Copy OTP",
                                copy_text: { text: otp }
                            },
                            {
                                text: "📢 Join Channel",
                                url: CHANNEL_LINK
                            }
                        ]
                    ]
                }
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.ok && data.result && data.result.message_id) {
                // 2 মিনিট পর মেসেজ ডিলিট হবে
                setTimeout(() => {
                    deleteMessage(data.result.message_id);
                }, DELETE_AFTER);
            }
        })
        .catch(e => console.log("Send Error:", e));
    }

    function checkSms() {
        document.querySelectorAll('tr').forEach(function(row) {
            let cols = row.querySelectorAll('td');
            if (cols.length >= 5) {
                let live = cols[0].innerText.trim();
                let sid = cols[1].innerText.trim();
                let msg = cols[4].innerText.trim();

                let uid = live + "_" + msg;

                if (msg && msg.length > 5 && sentSmsIds.indexOf(uid) === -1) {
                    sentSmsIds.push(uid);
                    if (sentSmsIds.length > 80) sentSmsIds.shift();
                    localStorage.setItem('sent_sms_ids_v17', JSON.stringify(sentSmsIds));

                    let c = getCountryInfo(live);
                    let service = getServiceDetails(sid, msg);

                    let phoneMatch = live.match(/\d{8,15}/);
                    let fullPhone = phoneMatch ? phoneMatch[0] : "";
                    let hiddenPhone = hidePhoneNumber(fullPhone);
                    let prefixPhone = fullPhone.length >= 5 ? fullPhone.slice(0, 5) : fullPhone;

                    let otpMatch = msg.match(/\b\d{3}[-\s]?\d{3}\b|\b\d{4,8}\b/);
                    let otp = otpMatch ? otpMatch[0] : "OTP";

                    let cleanMsg = msg.replace(/</g, "&lt;").replace(/>/g, "&gt;");

                    // ========== সুন্দর মেসেজ ফরম্যাট ==========
                    let text = `\( {service.emoji} <b> \){service.name}</b> ${c.flag}\n` +
                               `━━━━━━━━━━━━━━━━━━━━\n` +
                               `📱 <b>Number:</b> <code>${hiddenPhone}</code>\n` +
                               `🔍 <b>Prefix:</b> <code>+${prefixPhone}</code>\n` +
                               `🔑 <b>OTP:</b> <code>${otp}</code>\n` +
                               `━━━━━━━━━━━━━━━━━━━━\n` +
                               `<blockquote>${cleanMsg}</blockquote>\n` +
                               `⏳ <i>This message will auto-delete in 2 minutes</i>`;

                    sendToTelegram(text, otp, service.emoji);
                }
            }
        });
    }

    const observer = new MutationObserver(function() {
        checkSms();
    });

    observer.observe(document.body, { childList: true, subtree: true });
    setInterval(checkSms, CHECK_INTERVAL);
})();
