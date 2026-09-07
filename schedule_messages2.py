import telebot
import schedule
import threading
import time
import logging
from datetime import datetime
import pytz

logging.basicConfig(level=logging.INFO)

# --- CONFIGURATION ---
API_TOKEN = '8610888459:AAECtNwliQ1ZTiRoMVC9P8Vw6c70QVpMdyU'
TARGET_GROUP_ID = -1003995771127 
ADMIN_ID = 8626582205  

# ADD THE TELEGRAM IDs OF YOUR TRUSTED MEMBERS HERE
# Example: AUTHORIZED_USERS = [123456789, 987654321]
AUTHORIZED_USERS = [7430762303] 

IST_STR = 'Asia/Kolkata'
IST = pytz.timezone(IST_STR)

bot = telebot.TeleBot(API_TOKEN)
schedules_list = [] 

# --- CORE ACTIONS ---

def execute_scheduled_task(task_content):
    try:
        task_parts = task_content.strip().split()
        command = task_parts[0].lower()
        
        # 1. LOCK GROUP
        if command == 'lock':
            bot.set_chat_permissions(TARGET_GROUP_ID, telebot.types.ChatPermissions(can_send_messages=False))
            bot.send_message(TARGET_GROUP_ID, "🔒 **Group is now Locked.**", parse_mode="Markdown")
            logging.info("Task Executed: Locked")

        # 2. UNLOCK GROUP
        elif command == 'unlock':
            bot.set_chat_permissions(TARGET_GROUP_ID, telebot.types.ChatPermissions(
                can_send_messages=True, 
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            ))
            bot.send_message(TARGET_GROUP_ID, "🔓 **Group is now Unlocked.**", parse_mode="Markdown")
            logging.info("Task Executed: Unlocked")

        # 3. PROMOTE MEMBER (Usage: promote 12345678)
        elif command == 'promote':
            if len(task_parts) < 2: return
            user_id = int(task_parts[1])
            bot.promote_chat_member(
                TARGET_GROUP_ID, user_id,
                can_change_info=False, can_post_messages=True,
                can_edit_messages=True, can_delete_messages=True,
                can_invite_users=True, can_restrict_members=True,
                can_pin_messages=True, can_promote_members=False
            )
            bot.send_message(TARGET_GROUP_ID, f"✅ User <code>{user_id}</code> has been promoted to Admin.", parse_mode="HTML")
            logging.info(f"Task Executed: Promoted {user_id}")

        # 4. DISMISS MEMBER (Usage: dismiss 12345678)
        elif command == 'dismiss':
            if len(task_parts) < 2: return
            user_id = int(task_parts[1])
            # Resetting to standard member permissions
            bot.promote_chat_member(
                TARGET_GROUP_ID, user_id,
                can_change_info=False, can_post_messages=False,
                can_edit_messages=False, can_delete_messages=False,
                can_invite_users=False, can_restrict_members=False,
                can_pin_messages=False, can_promote_members=False
            )
            bot.send_message(TARGET_GROUP_ID, f"❌ User <code>{user_id}</code> has been dismissed from Admin.", parse_mode="HTML")
            logging.info(f"Task Executed: Dismissed {user_id}")

        # 5. REGULAR MESSAGE
        else:
            bot.send_message(TARGET_GROUP_ID, task_content)
            logging.info(f"Task Executed: Sent Message: {task_content}")
            
    except Exception as e:
        logging.error(f"Execution Error: {e}")

# --- HELPER FUNCTIONS ---

def add_to_schedule_list(time_str, content):
    """Register the task using IST timezone"""
    job_tag = f"job_{time_str}_{content[:10]}"
    
    # Force the scheduler to use Asia/Kolkata
    schedule.every().day.at(time_str, IST_STR).do(execute_scheduled_task, content).tag(job_tag)
    
    schedules_list.append({
        "id": job_tag,
        "time": time_str,
        "content": content
    })

# Updated to check both ADMIN_ID and AUTHORIZED_USERS list
def is_authorized(message):
    user_id = message.from_user.id
    return user_id == ADMIN_ID or user_id in AUTHORIZED_USERS

# --- COMMAND HANDLERS ---

@bot.message_handler(commands=['new_s'])
def handle_multi_schedule(message):
    if not is_authorized(message):
        return

    # Extract input after /new_s
    raw_input = message.text.replace('/new_s', '').strip()
    
    if not raw_input:
        bot.reply_to(message, "⚠️ **Usage:**\n`/new_s 03:00 lock | 05:00 unlock | 17:00 Message`", parse_mode="Markdown")
        return

    # Split by '|' to support multiple schedules in one message
    items = raw_input.split('|')
    success_count = 0
    fail_count = 0

    for item in items:
        item = item.strip()
        parts = item.split(maxsplit=1)
        
        if len(parts) == 2:
            time_str = parts[0]
            content = parts[1]
            
            try:
                # Validate time format (HH:MM)
                datetime.strptime(time_str, "%H:%M")
                add_to_schedule_list(time_str, content) 
                success_count += 1
            except ValueError:
                fail_count += 1
        else:
            fail_count += 1

    bot.reply_to(message, f"✅ **Processed!**\nAdded: {success_count}\nFailed/Errors: {fail_count}", parse_mode="HTML")

@bot.message_handler(commands=['list_s'])
def list_schedules(message):
    if not is_authorized(message):
        return

    if not schedules_list:
        bot.reply_to(message, "📋 No active schedules.")
        return
    
    current_ist = datetime.now(IST).strftime('%H:%M')
    response = f"📋 **Current Schedules (IST: {current_ist}):**\n"
    for i, s in enumerate(schedules_list, 1):
        response += f"{i}. `{s['time']}` - {s['content']}\n"
    bot.reply_to(message, response, parse_mode="HTML")

@bot.message_handler(commands=['remove_s'])
def remove_schedule(message):
    if not is_authorized(message):
        return

    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "❌ Use: `/remove_s 1` or `/remove_s all`", parse_mode="HTML")
        return

    target = command_parts[1].lower()

    # Option: Remove ALL schedules
    if target == "all":
        schedule.clear() # Clears all background jobs
        schedules_list.clear() # Clears the display list
        bot.reply_to(message, "🗑️ **All schedules have been cleared.**", parse_mode="Markdown")
        logging.info("All tasks removed by Authorized User.")
        return

    # Option: Remove by Index
    try:
        index = int(target) - 1
        if 0 <= index < len(schedules_list):
            removed = schedules_list.pop(index)
            schedule.clear(removed['id']) # Clears specific job by tag
            bot.reply_to(message, f"🗑️ Removed #{index + 1}: {removed['content']}")
        else:
            bot.reply_to(message, "❌ Serial number not found.")
    except ValueError:
        bot.reply_to(message, "❌ Use a number or 'all'. Example: `/remove_s 1`", parse_mode="Markdown")

@bot.message_handler(commands=['help_s'])
def echo_help(message):
    # Optional: You can also restrict the help command to authorized users if you want
    if not is_authorized(message):
        return
        
    help_text = (
        "✨ **Schedule Bot Help**\n"
        "• `/new_s 03:00 lock | 05:00 unlock` - Multi-schedule\n"
        "• `/list_s` - Show active tasks\n"
        "• `/remove_s 1` - Remove by serial number\n"
        "• Time must be in **24-hour format** (e.g., 17:00 for 5 PM)."
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

# --- RUNNER ---

def run_scheduler():
    while True:
        # Check every 5 seconds if a task is due
        schedule.run_pending()
        time.sleep(5)

if __name__ == "__main__":
    logging.info(f"Scheduler Bot Started. Owner ID: {ADMIN_ID}")
    # Run the schedule loop in a background thread
    threading.Thread(target=run_scheduler, daemon=True).start()
    
    print("🚀 Schedule Bot is live with continuous connection fallbacks...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
