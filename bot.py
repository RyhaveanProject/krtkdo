#!/usr/bin/env python3
"""
Gamee KarateKido Score Hack - Telegram Bot
Authorized Pentest Tool - User ID: 8223756945
"""

import telebot
import requests
import json
import hashlib
import re
import time
import uuid as uuid_lib
from datetime import datetime, timezone, timedelta

# ==================== KONFIGÜRASYON ====================
TOKEN = "8638965074:AAGkXepPHGUq5F7JAEeykJselAuMX-ZZe1w"
BOT_OWNER_ID = 8223756945
GAMEE_API = "https://api.service.gameeapp.com"
SECRET_KEY = "crmjbjm3lczhlgnek9uaxz2l9svlfjw14npauhen"
GAME_ID = 212  # KarateKido

bot = telebot.TeleBot(TOKEN)
pending_link = {}

# ==================== MD5 IMPLEMENTATION ====================
def md5(text):
    return hashlib.md5(text.encode()).hexdigest()

# ==================== CHECKSUM ====================
def get_checksum(score, play_time, game_url, game_state_data):
    raw = f"{score}:{play_time}:{game_url}:{game_state_data}:{SECRET_KEY}"
    return md5(raw)

# ==================== UUID'YI LINKTEN ÇIKAR ====================
def extract_uuid_from_link(link):
    """Telegram start parametresinden veya linkten UUID/startParam çeker"""
    # https://t.me/gamee/game?startapp=eyJ... formatı
    match = re.search(r'startapp=([^&\s]+)', link)
    if match:
        import base64
        try:
            encoded = match.group(1)
            # URL Safe Base64 padding
            padding = 4 - len(encoded) % 4
            if padding != 4:
                encoded += '=' * padding
            decoded = base64.urlsafe_b64decode(encoded)
            data = json.loads(decoded)
            slug = data.get('game', {}).get('slg', '')
            return slug
        except:
            pass
    
    # Alternatif: /game/ formatı
    match = re.search(r'/game/([^&\s?#]+)', link)
    if match:
        return match.group(1)
    
    return None

# ==================== GAMEE API İŞLEMLERİ ====================
def get_auth_token(game_url_path, install_uuid):
    """Gamee API'den authentication token alır"""
    auth_data = {
        "jsonrpc": "2.0",
        "id": "user.authentication.botLogin",
        "method": "user.authentication.botLogin",
        "params": {
            "botName": "telegram",
            "botGameUrl": game_url_path,
            "botUserIdentifier": None
        }
    }
    
    headers = {
        'Content-Type': 'text/plain;charset=UTF-8',
        'X-Install-Uuid': install_uuid
    }
    
    try:
        resp = requests.post(GAMEE_API, headers=headers, data=json.dumps(auth_data), timeout=15)
        resp_json = resp.json()
        token = resp_json.get('result', {}).get('tokens', {}).get('authenticate')
        return token
    except Exception as e:
        print(f"[!] Auth error: {e}")
        return None

def send_fake_score(auth_token, score, play_time, game_url, install_uuid, gameplay_id):
    """Gamee API'ye fake score gönderir"""
    game_state_data = f'{{"totalBlockCnt":{score}}}'
    game_url_path = f"/game/{game_url}"
    
    # Zaman: şimdi + 2 saat (Gamee timezone)
    now = datetime.now(timezone.utc) + timedelta(hours=2)
    created_time = now.strftime("%Y-%m-%dT%H:%M:%S") + "+02:00"
    
    checksum = get_checksum(score, play_time, game_url_path, game_state_data)
    
    payload = {
        "jsonrpc": "2.0",
        "id": "game.saveWebGameplay",
        "method": "game.saveWebGameplay",
        "params": {
            "gameplayData": {
                "gameId": GAME_ID,
                "score": score,
                "playTime": play_time,
                "gameUrl": game_url_path,
                "metadata": {
                    "gameplayId": gameplay_id,
                },
                "releaseNumber": 8,
                "gameStateData": game_state_data,
                "createdTime": created_time,
                "checksum": checksum,
                "replayVariant": None,
                "replayData": None,
                "replayDataChecksum": None,
                "isSaveState": False,
                "gameplayOrigin": "game"
            }
        }
    }
    
    headers = {
        'Content-Type': 'text/plain;charset=UTF-8',
        'authorization': f'Bearer {auth_token}'
    }
    
    try:
        resp = requests.post(GAMEE_API, headers=headers, data=json.dumps(payload), timeout=15)
        return resp.json()
    except Exception as e:
        print(f"[!] Score send error: {e}")
        return None

# ==================== TELEGRAM BOT HANDLER ====================
@bot.message_handler(commands=['start'])
def start_handler(message):
    if message.from_user.id != BOT_OWNER_ID:
        bot.reply_to(message, "❌ Bu bot sadece yetkili kullanıcı içindir.")
        return
    
    bot.reply_to(message, 
        "🎯 *KarateKido Score Hack Active*\n\n"
        "Lütfen oyun linkini gönder:\n"
        "`https://t.me/gamee/game?startapp=...`\n\n"
        "Bot UUID'yi otomatik çekecek ve hack'i başlatacak!",
        parse_mode='Markdown'
    )
    pending_link[message.chat.id] = True

@bot.message_handler(func=lambda msg: msg.chat.id in pending_link and pending_link[msg.chat.id])
def link_handler(message):
    if message.from_user.id != BOT_OWNER_ID:
        return
    
    link = message.text.strip()
    bot.reply_to(message, "🔍 Link analiz ediliyor...")
    
    # UUID/Slug'ı linkten çıkar
    slug = extract_uuid_from_link(link)
    if not slug:
        bot.reply_to(message, "❌ Linkten UUID çözülemedi. Geçerli bir Gamee linki gönderin.")
        return
    
    bot.send_message(message.chat.id, f"✅ Oyun Slug: `{slug}`\n🚀 Score hack başlatılıyor...", parse_mode='Markdown')
    
    # Rastgele bir install UUID oluştur
    install_uuid = str(uuid_lib.uuid4())
    game_url_path = f"/game/{slug}"
    
    # Auth token al
    token = get_auth_token(game_url_path, install_uuid)
    if not token:
        bot.send_message(message.chat.id, "❌ Authentication başarısız. Telegram'da oyunu açıp tekrar dene.")
        del pending_link[message.chat.id]
        return
    
    bot.send_message(message.chat.id, "✅ Authentication başarılı! Score gönderiliyor...")
    
    # Kullanıcıya rastgele ama mantıklı gameplayId
    gameplay_id = int(time.time() * 1000) % 1000000
    
    # 1 MİLYON SCORE - ama playTime mantıklı olmalı
    million_score = 1000000
    play_time = 120  # 2 dakika gibi makul
    
    bot.send_message(message.chat.id, f"📊 Score: `{million_score:,}` gönderiliyor...", parse_mode='Markdown')
    
    # İlk deneme
    result = send_fake_score(token, million_score, play_time, slug, install_uuid, gameplay_id)
    
    if result and 'result' in result:
        bot.send_message(message.chat.id, 
            f"✅ *BAŞARILI!*\n\n"
            f"🎯 Score: `{million_score:,}`\n"
            f"⏱ Play Time: {play_time}s\n"
            f"🆔 Gameplay ID: {gameplay_id}\n\n"
            f"📱 Oyunu aç ve leaderboard'u kontrol et!",
            parse_mode='Markdown'
        )
    else:
        error_msg = result.get('error', {}).get('message', 'Bilinmeyen hata') if result else 'Yanıt alınamadı'
        bot.send_message(message.chat.id, f"⚠️ İlk deneme başarısız: {error_msg}\nAlternatif yöntem deneniyor...")
        
        # Alternatif: daha düşük score dene
        alt_score = 999999
        alt_result = send_fake_score(token, alt_score, 90, slug, install_uuid, gameplay_id + 1)
        
        if alt_result and 'result' in alt_result:
            bot.send_message(message.chat.id, 
                f"✅ *ALTERNATİF BAŞARILI!*\n\n"
                f"🎯 Score: `{alt_score:,}`\n"
                f"⏱ Play Time: 90s\n\n"
                f"📱 Şimdi oyunu aç ve kontrol et!",
                parse_mode='Markdown'
            )
        else:
            bot.send_message(message.chat.id, 
                "⚠️ Her iki yöntem de başarısız. Şunları dene:\n"
                "1️⃣ Telegram'da oyunu aç (hiç oynamasan bile)\n"
                "2️⃣ Linki tekrar gönder\n"
                "3️⃣ Telefon/tablet yerine PC'den Telegram kullan"
            )
    
    del pending_link[message.chat.id]

@bot.message_handler(func=lambda msg: msg.chat.id not in pending_link)
def unknown_handler(message):
    if message.from_user.id == BOT_OWNER_ID:
        bot.reply_to(message, "💡 /start yazıp link gönderme talimatlarını alabilirsin.")

# ==================== MAIN ====================
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════╗
    ║     🥋 KARATE KIDO SCORE HACK       ║
    ║        Telegram Bot v1.0             ║
    ║     Authorized Pentest Tool          ║
    ╚══════════════════════════════════════╝
    """)
    print("[*] Bot başlatılıyor...")
    print(f"[*] Hedef Kullanıcı ID: {BOT_OWNER_ID}")
    print("[*] Bekleniyor... Telegram'da @bot ile konuş")
    
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("\n[!] Bot durduruldu.")
