import telebot
import json
import threading
import os
import time
from datetime import datetime, timedelta

# Configuration
TOKEN = "8849698407:AAG8oYPx7UQ3T4Jw-UeyQLBZYGgPv9RmFTk"
FREE_GROUP_ID = -1004490201684 # Your free group ID
FEEDBACK_DB_PATH = "/home/dx3/bot_data_tobi/pending_feedback.json"
ADMIN_ID = 8286263795
bot = telebot.TeleBot(TOKEN)

# Constants for persistent storage
SETTINGS_PATH = "/home/dx3/bot_data_tobi/settings.json"
ALLOWED_REVIEWERS_PATH = "/home/dx3/bot_data_tobi/reviewers.json"

def get_auto_approve_time():
    settings = load_json(SETTINGS_PATH, {"auto_approve_time": 300})
    return settings.get("auto_approve_time", 300)

def set_auto_approve_time(seconds):
    settings = load_json(SETTINGS_PATH, {})
    settings["auto_approve_time"] = seconds
    save_json(SETTINGS_PATH, settings)

def get_reviewers():
    return load_json(ALLOWED_REVIEWERS_PATH, {"ids": [ADMIN_ID]})["ids"]

def add_reviewer(user_id):
    reviewers = load_json(ALLOWED_REVIEWERS_PATH, {"ids": [ADMIN_ID]})
    if user_id not in reviewers["ids"]:
        reviewers["ids"].append(user_id)
        save_json(ALLOWED_REVIEWERS_PATH, reviewers)
        
        
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
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
        
    
def check_auto_approval():
    while True:
        data = load_json(FEEDBACK_DB_PATH, {})
        now = datetime.now()
        threshold = get_auto_approve_time()
        for uid, info in list(data.items()):
            if now - datetime.fromisoformat(info['time']) > timedelta(seconds=threshold):
                
                msg_id = info.get('group_msg_id')
                
                # 1. Edit group message
                try: bot.edit_message_text(f"✅ <b>USER:</b> {uid}\nStatus: <b>Auto-approved</b>", FREE_GROUP_ID, msg_id, parse_mode="HTML")
                except: pass
                
                # 2. DM user
                try: bot.send_message(uid, "✅ Your attack feedback was auto-approved. You can now attack!")
                except: pass
                
                del data[uid]
                save_json(FEEDBACK_DB_PATH, data)
        time.sleep(10)
@bot.message_handler(commands=['time'])
def set_time_command(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        new_time = int(message.text.split()[1])
        set_auto_approve_time(new_time)
        bot.reply_to(message, f"✅ Auto-approval time set to {new_time} seconds.")
    except: bot.reply_to(message, "⚠️ Usage: /time <seconds>")

@bot.message_handler(commands=['adduser'])
def add_user_command(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        target_id = int(message.text.split()[1])
        add_reviewer(target_id)
        bot.reply_to(message, f"✅ User {target_id} added to reviewers.")
    except: bot.reply_to(message, "⚠️ Usage: /adduser <userid>")
    
    
@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    if message.chat.id != FREE_GROUP_ID: return
    
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    data = load_json(FEEDBACK_DB_PATH, {})
    
    # 🔥 NEW: Check if the user already has a pending request
    if str(user_id) in data:
        # Calculate how much time is left for auto-approval
        entry_time = datetime.fromisoformat(data[str(user_id)]['time'])
        elapsed = (datetime.now() - entry_time).total_seconds()
        remaining = max(0, 300 - int(elapsed))
        
        bot.reply_to(
            message, 
            f"⚠️ <b>Already Pending!</b>\n"
            f"You have already sent feedback. Please wait for approval or wait <b>{remaining} seconds</b> for auto-approval.\n\n"
            f"📩 You will receive a DM in @feedback_verification_bot once approved.", 
            parse_mode="HTML"
        )
        return 
        
    # 1. Notify the group immediately that the user is waiting
    status_msg = bot.send_message(
        FREE_GROUP_ID, 
        f"⏳ <b>USER:</b> @{username} ({user_id})\nStatus: <b>Waiting for approval...</b>\n<i>Auto Approved in 300 seconds if no action taken by owner.</i>", 
        parse_mode="HTML"
    )
    
    # 2. Save the message ID in the JSON
    data[str(user_id)] = {
        "username": username,
        "time": datetime.now().isoformat(),
        "group_msg_id": status_msg.message_id
    }
    save_json(FEEDBACK_DB_PATH, data)
    
    # 3. Send screenshot to Admin DM
      # Send photo to all reviewers
    for r_id in get_reviewers():
        try:
            bot.send_photo(r_id, message.photo[-1].file_id, 
                           caption=f"Verify Feedback for @{username} ({user_id})",
                           reply_markup=create_approval_markup(user_id, status_msg.message_id))
        except: pass

def create_approval_markup(user_id, msg_id):
    markup = telebot.types.InlineKeyboardMarkup()
    # Pass the message ID in the callback data so we know which message to edit
    markup.add(telebot.types.InlineKeyboardButton("✅ Approve", callback_data=f"app|{user_id}|{msg_id}"))
    markup.add(telebot.types.InlineKeyboardButton("❌ Deny", callback_data=f"den|{user_id}|{msg_id}"))
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    action, user_id, group_msg_id = call.data.split('|')
    data = load_json(FEEDBACK_DB_PATH, {})
    
    # Check if already processed
    if data.get(user_id, {}).get('status') in ['approved', 'denied']:
        bot.answer_callback_query(call.id, "❌ Already handled!")
        return

    # 1. Determine status text
    status_text = "Approved" if action == "app" else "Rejected"
    emoji = "✅" if action == "app" else "❌"
    
    # 2. Update the original Admin DM message
    # This removes the photo and buttons, replacing them with text
    
# 2. Update the original Admin/Reviewer DM message
    reviewers = get_reviewers()
    for r_id in reviewers:
        try:
            bot.edit_message_caption(
                chat_id=r_id, 
                message_id=call.message.message_id, 
                caption=f"{emoji} Feedback for {user_id} was {status_text} by @{call.from_user.username}."
            )
        except: pass # Message might not exist for some reviewers

    # 3. Update the Group message status
    if action == "app":
        data[user_id]['status'] = 'approved'
        data[user_id]['reviewed_by'] = call.from_user.username
        bot.edit_message_text(f"✅ <b>USER:</b> {user_id}\nStatus: <b>Approved by @{call.from_user.username}</b>", FREE_GROUP_ID, int(group_msg_id), parse_mode="HTML")
        try: bot.send_message(user_id, "✅ Your attack feedback has been approved. You can now attack!")
        except: pass
    else:
        data[user_id]['status'] = 'denied'
        data[user_id]['reviewed_by'] = call.from_user.username
        bot.edit_message_text(f"❌ <b>USER:</b> {user_id}\nStatus: <b>Rejected by @{call.from_user.username}</b>", FREE_GROUP_ID, int(group_msg_id), parse_mode="HTML")
        try: bot.send_message(user_id, "❌ Your feedback was rejected. Please send the correct screenshot.")
        except: pass
    
    save_json(FEEDBACK_DB_PATH, data) # Don't delete, just update status
    bot.answer_callback_query(call.id, "Feedback updated")

    # 4. Cleanup Database
    if user_id in data:
        del data[user_id]
        save_json(FEEDBACK_DB_PATH, data)
        
    bot.answer_callback_query(call.id, f"Feedback {status_text}")

    
if __name__ == "__main__":
    print("🚀 Feedback Bot is running...")
    
    # 1. Start the auto-approval loop in a background thread
    auto_approval_thread = threading.Thread(target=check_auto_approval, daemon=True)
    auto_approval_thread.start()
    
    # 2. Start the bot polling
    bot.infinity_polling(timeout=60, long_polling_timeout=60)