import telebot
import os
import json
from datetime import datetime

# ============ CONFIGURATION ============
BOT_TOKEN = "8760399314:AAHVXi7iEDFcmmM7YvbhoqyNFWM0pVKb9R0"
BOT_OWNER = 8626582205 

# ============ DATA SEPARATION ============
DATA_DIR = "bot_data_media_manager"
os.makedirs(DATA_DIR, exist_ok=True)
LIBRARY_FILE = os.path.join(DATA_DIR, "media_library.json")

bot = telebot.TeleBot(BOT_TOKEN)

# ============ HELPER FUNCTIONS ============
def load_json(file_path, default=None):
    if default is None: default = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f: return json.load(f)
        except: return default
    return default

def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

# ============ PUBLIC COMMANDS ============

@bot.message_handler(commands=['get'])
def send_media_from_library(message):
    library = load_json(LIBRARY_FILE, {})
    command_parts = message.text.split()
    
    if len(command_parts) != 2:
        if not library:
            bot.reply_to(message, "❌ No items available.")
            return
        keys_list = "\n".join([f"• `/get {name}`" for name in library.keys()])
        bot.reply_to(message, f"📂 **Available Items:**\n\n{keys_list}", parse_mode="Markdown")
        return

    name = command_parts[1].lower()
    if name in library:
        item = library[name]
        
        # Explicit extraction logic to keep types strictly separated
        if isinstance(item, dict):
            file_id = item.get("file_id")
            file_type = item.get("type", "document")
        else:
            # Safe handling for older plain string database entries
            file_id = str(item)
            file_type = 'document'

        # Safety Check: If file_id extraction failed entirely
        if not file_id:
            bot.reply_to(message, "❌ Error: The database entry for this asset is corrupt.")
            return

        caption_text = f"📂 Asset: `{name}`"
        try:
            # Smart dispatch routing using guaranteed string IDs
            if file_type == 'photo':
                bot.send_photo(message.chat.id, file_id, caption=caption_text, parse_mode="Markdown")
            elif file_type == 'video':
                bot.send_video(message.chat.id, file_id, caption=caption_text, parse_mode="Markdown")
            elif file_type == 'audio':
                bot.send_audio(message.chat.id, file_id, caption=caption_text, parse_mode="Markdown")
            elif file_type == 'voice':
                bot.send_voice(message.chat.id, file_id, caption=caption_text, parse_mode="Markdown")
            else:
                # Delivers your APK files flawlessly through the native stream channel
                bot.send_document(message.chat.id, file_id, caption=caption_text, parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to send file entity. Error: {e}")
    else:
        bot.reply_to(message, "❌ Item not found.", parse_mode="Markdown")


# ============ OWNER ONLY COMMANDS ============

@bot.message_handler(commands=['del'])
def delete_media_from_library(message):
    if message.from_user.id != BOT_OWNER: return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "⚠️ Usage: `/del <name>`")
        return
    
    name = command_parts[1].lower()
    library = load_json(LIBRARY_FILE, {})
    if name in library:
        del library[name]
        save_json(LIBRARY_FILE, library)
        bot.reply_to(message, f"✅ `{name}` deleted.")
    else:
        bot.reply_to(message, "❌ Not found.")

@bot.message_handler(content_types=['document', 'photo', 'video', 'audio', 'voice', 'video_note'])
def handle_incoming_media(message):
    # 1. First, check if it's the owner
    if message.from_user.id != BOT_OWNER:
        return
    
    # 2. Only proceed if the chat type is 'private'
    if message.chat.type != "private":
        return

    msg = bot.reply_to(message, "✅ **Media Received!** What name should I save this as?")
    
    # 🔥 FIXED: Pass the entire 'message' object instead of 'message.message_id'
    bot.register_next_step_handler(msg, process_media_name, message)


def get_file_id(message):
    """Helper to extract file_id and content_type from any media type"""
    if message.content_type == 'photo': 
        return message.photo[-1].file_id, 'photo'
    elif message.content_type == 'audio': 
        return message.audio.file_id, 'audio'
    elif message.content_type == 'voice': 
        return message.voice.file_id, 'voice'
    elif message.content_type == 'video': 
        return message.video.file_id, 'video'
    elif message.content_type == 'document': 
        return message.document.file_id, 'document'
    return None, None


def process_media_name(message, original_msg):
    if message.from_user.id != BOT_OWNER: return
    name = message.text.lower().strip()
    
    # Receives BOTH the file_id and the type perfectly now
    f_id, c_type = get_file_id(original_msg)
    
    if not f_id:
        bot.reply_to(message, "❌ Could not extract File ID.")
        return

    library = load_json(LIBRARY_FILE, {})
    
    # Structure it as a dictionary so /get knows how to send it natively
    library[name] = {
        "file_id": f_id,
        "type": c_type
    }
    
    save_json(LIBRARY_FILE, library)
    bot.reply_to(message, f"✅ Saved as `{name}` with type reference.")


# ============ BOT START ============
if __name__ == "__main__":
    print("🚀 Media Manager is Running with Network Fallbacks...")
    # ✅ FIXED: We removed non_stop=True since infinity_polling handles it automatically!
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
