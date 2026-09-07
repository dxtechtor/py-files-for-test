import json
import os
import html
import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==========================================
# ⚙️ CONFIGURATION & SETUP
# ==========================================
BOT_TOKEN = "8730956259:AAFuW-Iqrnmz58ks1IEya-4Ud2Y3im84LTk"
# Put YOUR Telegram User ID here so you can use /addadmin and /approve_group
BOT_OWNER_ID = 8626582205 

POINTS_FILE = "arcade_points.json"
ADMINS_FILE = "arcade_admins.json"
APPROVED_GROUPS_FILE = "approved_groups.json"

# --- Persistent Points Storage ---
def load_points():
    if os.path.exists(POINTS_FILE):
        with open(POINTS_FILE, "r") as file:
            try:
                data = json.load(file)
                for k, v in data.items():
                    if isinstance(v, int):
                        data[k] = {"points": v, "name": f"User_{k}"}
                return data
            except json.JSONDecodeError:
                return {}
    return {}

def save_points(points_data):
    with open(POINTS_FILE, "w") as file:
        json.dump(points_data, file, indent=4)

# --- Persistent Admins Storage ---
def load_admins():
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    return []

def save_admins(admins_list):
    with open(ADMINS_FILE, "w") as file:
        json.dump(admins_list, file, indent=4)

# --- Persistent Approved Groups Storage ---
def load_approved_groups():
    if os.path.exists(APPROVED_GROUPS_FILE):
        with open(APPROVED_GROUPS_FILE, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    return []

def save_approved_groups(groups_list):
    with open(APPROVED_GROUPS_FILE, "w") as file:
        json.dump(groups_list, file, indent=4)

# Global Memory 
active_games = {}
user_points = load_points()

def apply_global_points(user_id, user_name, points):
    user_id_str = str(user_id)
    if user_id_str not in user_points:
        user_points[user_id_str] = {"points": 0, "name": user_name}
    user_points[user_id_str]["points"] += points
    user_points[user_id_str]["name"] = user_name
    save_points(user_points)

def get_player_info(user):
    return html.escape(user.full_name)

def safe_remove_job(job):
    if job:
        try:
            job.schedule_removal()
        except Exception:
            pass

# ==========================================
# 🛡️ SECURITY & APPROVAL CHECKS
# ==========================================
async def check_approval(update: Update) -> bool:
    """Checks if the chat is approved to use the bot."""
    chat_id = update.effective_chat.id
    
    # Always allow the Bot Owner in private chat to manage the bot
    if update.effective_chat.type == "private" and update.effective_user.id == BOT_OWNER_ID:
        return True
        
    approved_groups = load_approved_groups()
    if chat_id not in approved_groups:
        try:
            # Provide the group ID so they can ask the owner to approve it
            text = f"❌ <b>Group Not Approved!</b>\n\nThis bot is private. Ask the Bot Owner @dxtechtor_owner to approve this group by sending them this ID:\n\n<code>{chat_id}</code>"
            await update.message.reply_text(text, parse_mode="HTML")
        except Exception:
            pass
        return False
    return True

async def approve_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != BOT_OWNER_ID:
        return await update.message.reply_text("❌ Only the Bot Owner can approve groups.")

    if not context.args:
        return await update.message.reply_text("⚠️ Usage: /approve_group <group_id>")

    try:
        group_id = int(context.args[0])
    except ValueError:
        return await update.message.reply_text("⚠️ Group ID must be a valid number (e.g., -100123456789).")

    groups = load_approved_groups()
    if group_id not in groups:
        groups.append(group_id)
        save_approved_groups(groups)
        await update.message.reply_text(f"✅ Group ID <code>{group_id}</code> has been approved!", parse_mode="HTML")
    else:
        await update.message.reply_text("ℹ️ That group is already approved.")

async def dismiss_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != BOT_OWNER_ID:
        return await update.message.reply_text("❌ Only the Bot Owner can dismiss groups.")

    if not context.args:
        return await update.message.reply_text("⚠️ Usage: /dismiss_group <group_id>")

    try:
        group_id = int(context.args[0])
    except ValueError:
        return await update.message.reply_text("⚠️ Group ID must be a valid number.")

    groups = load_approved_groups()
    if group_id in groups:
        groups.remove(group_id)
        save_approved_groups(groups)
        await update.message.reply_text(f"✅ Group ID <code>{group_id}</code> has been removed/dismissed.", parse_mode="HTML")
    else:
        await update.message.reply_text("ℹ️ That group is not in the approved list.")

# ==========================================
# 🛡️ ADMIN MANAGEMENT
# ==========================================
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != BOT_OWNER_ID:
        await update.message.reply_text("❌ Only the Bot Owner can add admins.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Usage: /addadmin <userid>")
        return

    new_admin_id = context.args[0]
    admins = load_admins()
    
    if new_admin_id not in admins:
        admins.append(new_admin_id)
        save_admins(admins)
        await update.message.reply_text(f"✅ User ID {new_admin_id} is now an Arcade Admin.")
    else:
        await update.message.reply_text("ℹ️ That user is already an admin.")

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != BOT_OWNER_ID:
        await update.message.reply_text("❌ Only the Bot Owner can remove admins.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Usage: /removeadmin <userid>")
        return

    target_id = context.args[0]
    admins = load_admins()
    
    if target_id in admins:
        admins.remove(target_id)
        save_admins(admins)
        await update.message.reply_text(f"✅ User ID {target_id} has been removed from admins.")
    else:
        await update.message.reply_text("ℹ️ That user is not in the admin list.")

# ==========================================
# 1️⃣ TIC-TAC-TOE (XO) LOGIC
# ==========================================
XO_EMPTY = '⬜'
XO_P1 = '❌'
XO_P2 = '⭕'

def check_xo_win(b, p):
    win_states = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    return any(b[i] == b[j] == b[k] == p for i, j, k in win_states)

def get_xo_markup(board):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(board[0], callback_data="xo_0"), InlineKeyboardButton(board[1], callback_data="xo_1"), InlineKeyboardButton(board[2], callback_data="xo_2")],
        [InlineKeyboardButton(board[3], callback_data="xo_3"), InlineKeyboardButton(board[4], callback_data="xo_4"), InlineKeyboardButton(board[5], callback_data="xo_5")],
        [InlineKeyboardButton(board[6], callback_data="xo_6"), InlineKeyboardButton(board[7], callback_data="xo_7"), InlineKeyboardButton(board[8], callback_data="xo_8")]
    ])

async def cmd_xo_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_approval(update): return
    text = "🎮 <b>Tic-Tac-Toe Rules</b> 🎮\n\nClassic 3x3 grid. Connect 3 pieces in a row horizontally, vertically, or diagonally to win!\n🏆 <b>Win Reward:</b> +5 points\n\n<b>Commands:</b>\n• /xo - Start game\n• /xoclose - Force close game\n• /xorules - Show rules"
    await update.message.reply_text(text, parse_mode="HTML")

# ==========================================
# 2️⃣ CONNECT FOUR (C4) LOGIC
# ==========================================
C4_EMPTY = '⚪'
C4_P1 = '🔴'
C4_P2 = '🟡'

def check_c4_win(board, piece):
    for c in range(4):
        for r in range(6):
            if board[r*7+c] == piece and board[r*7+c+1] == piece and board[r*7+c+2] == piece and board[r*7+c+3] == piece: return True
    for c in range(7):
        for r in range(3):
            if board[r*7+c] == piece and board[(r+1)*7+c] == piece and board[(r+2)*7+c] == piece and board[(r+3)*7+c] == piece: return True
    for c in range(4):
        for r in range(3):
            if board[r*7+c] == piece and board[(r+1)*7+c+1] == piece and board[(r+2)*7+c+2] == piece and board[(r+3)*7+c+3] == piece: return True
    for c in range(4):
        for r in range(3, 6):
            if board[r*7+c] == piece and board[(r-1)*7+c+1] == piece and board[(r-2)*7+c+2] == piece and board[(r-3)*7+c+3] == piece: return True
    return False

def drop_c4_piece(board, col, piece):
    for r in range(5, -1, -1):
        if board[r*7 + col] == C4_EMPTY:
            board[r*7 + col] = piece
            return True
    return False 

def get_c4_markup(board):
    keyboard = []
    for r in range(6):
        row = [InlineKeyboardButton(board[r*7 + c], callback_data=f"c4_{c}") for c in range(7)]
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

async def cmd_c4_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_approval(update): return
    text = "🎮 <b>Connect Four Rules</b> 🎮\n\nTap ANY button in a column. Your piece will fall to the lowest empty spot. Connect 4 pieces in any direction to win!\n🏆 <b>Win Reward:</b> +15 points\n\n<b>Commands:</b>\n• /c4 - Start game\n• /c4close - Force close game\n• /c4rules - Show rules"
    await update.message.reply_text(text, parse_mode="HTML")

# ==========================================
# 3️⃣ BLIND RPS LOGIC
# ==========================================
RPS_EMOJIS = {'r': '🪨 Rock', 'p': '📜 Paper', 's': '✂️ Scissors'}
RPS_WINS = {'r': 's', 'p': 'r', 's': 'p'}

def get_rps_markup():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🪨 Rock", callback_data="rps_r"),
        InlineKeyboardButton("📜 Paper", callback_data="rps_p"),
        InlineKeyboardButton("✂️ Scissors", callback_data="rps_s")
    ]])

async def cmd_rps_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_approval(update): return
    text = "🎮 <b>Rock Paper Scissors Rules</b> 🎮\n\nTap your choice! The bot will secretly lock it in. Once both players tap, the choices are revealed!\n🪨 beats ✂️ | ✂️ beats 📜 | 📜 beats 🪨\n🏆 <b>Win Reward:</b> +10 points\n\n<b>Commands:</b>\n• /rps - Start game\n• /rpsclose - Force close game\n• /rpsrules - Show rules"
    await update.message.reply_text(text, parse_mode="HTML")

# ==========================================
# 4️⃣ OTHELLO / REVERSI LOGIC
# ==========================================
REV_SIZE = 6 
REV_EMPTY = '➖'   
REV_P1 = '⚫' 
REV_P2 = '⚪'

def init_rev_board():
    b = [REV_EMPTY] * 36
    b[14], b[15], b[20], b[21] = REV_P2, REV_P1, REV_P1, REV_P2
    return b

def get_rev_flips(board, r, c, piece):
    opponent = REV_P2 if piece == REV_P1 else REV_P1
    flips = []
    dirs = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    for dr, dc in dirs:
        nr, nc, temp = r + dr, c + dc, []
        while 0 <= nr < 6 and 0 <= nc < 6 and board[nr * 6 + nc] == opponent:
            temp.append(nr * 6 + nc)
            nr += dr
            nc += dc
        if 0 <= nr < 6 and 0 <= nc < 6 and board[nr * 6 + nc] == piece and temp:
            flips.extend(temp)
    return flips

def get_rev_valid(board, piece):
    return [i for i in range(36) if board[i] == REV_EMPTY and get_rev_flips(board, i//6, i%6, piece)]

def count_pieces(board):
    return board.count(REV_P1), board.count(REV_P2)

def get_rev_markup(board):
    return InlineKeyboardMarkup([[InlineKeyboardButton(board[r*6 + c], callback_data=f"rev_{r*6 + c}") for c in range(6)] for r in range(6)])

async def cmd_rev_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_approval(update): return
    text = "🎮 <b>Othello (Reversi) Rules</b> 🎮\n\nYou MUST place your piece to trap opponent pieces between yours. Trapped pieces flip to your color! Finish with the most pieces to win.\n🏆 <b>Win Reward:</b> +20 points\n\n<b>Commands:</b>\n• /reversi - Start game\n• /reversiclose - Force close game\n• /reversirules - Show rules"
    await update.message.reply_text(text, parse_mode="HTML")

# ==========================================
# 5️⃣ MINESWEEPER RAID LOGIC
# ==========================================
MS_SIZE = 8
MS_MINES = 10
MS_HIDDEN = '⬜'
MS_MINE = '💣'
MS_SAFE = '0️⃣' 
MS_NUMS = {1: '1️⃣', 2: '2️⃣', 3: '3️⃣', 4: '4️⃣', 5: '5️⃣', 6: '6️⃣', 7: '7️⃣', 8: '8️⃣'}

def init_ms_empty():
    return [0]*64, [MS_HIDDEN]*64

def generate_ms_board(clicked_idx):
    hidden = [0] * 64
    exclude = {clicked_idx}
    r, c = clicked_idx // 8, clicked_idx % 8
    dirs = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    for dr, dc in dirs:
        if 0 <= r+dr < 8 and 0 <= c+dc < 8: 
            exclude.add((r+dr)*8 + (c+dc))
    
    available = [i for i in range(64) if i not in exclude]
    if len(available) < MS_MINES: 
        available = [i for i in range(64) if i != clicked_idx]
    
    for m in random.sample(available, MS_MINES): 
        hidden[m] = 'M'
    
    for row in range(8):
        for col in range(8):
            idx = row * 8 + col
            if hidden[idx] == 'M': 
                continue
            count = sum(1 for dr, dc in dirs if 0 <= row+dr < 8 and 0 <= col+dc < 8 and hidden[(row+dr)*8 + (col+dc)] == 'M')
            hidden[idx] = count
    return hidden

def reveal_ms_cell(hidden, visible, idx):
    if visible[idx] != MS_HIDDEN: 
        return 0
    if hidden[idx] == 'M':
        visible[idx] = MS_MINE
        return -1 
    if hidden[idx] > 0:
        visible[idx] = MS_NUMS[hidden[idx]]
        return 1

    queue, revealed = [idx], 1
    visible[idx] = MS_SAFE
    dirs = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    while queue:
        curr = queue.pop(0)
        r, c = curr // 8, curr % 8
        for dr, dc in dirs:
            nr, nc = r+dr, c+dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                n_idx = nr * 8 + nc
                if visible[n_idx] == MS_HIDDEN:
                    if hidden[n_idx] == 0:
                        visible[n_idx] = MS_SAFE
                        queue.append(n_idx)
                    elif hidden[n_idx] != 'M':
                        visible[n_idx] = MS_NUMS[hidden[n_idx]]
                    revealed += 1
    return revealed

def get_ms_markup(visible):
    return InlineKeyboardMarkup([[InlineKeyboardButton(visible[r*8 + c], callback_data=f"ms_{r*8 + c}") for c in range(8)] for r in range(8)])

async def cmd_ms_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_approval(update): return
    text = "🎮 <b>Minesweeper Raid Rules</b> 🎮\n\n✅ <b>+1 Point</b> for every safe tile or number you reveal.\n0️⃣ <b>Safe Zones:</b> Zeroes (0️⃣) mean NO mines nearby and trigger huge combos!\n💥 <b>SUDDEN DEATH:</b> Click a Mine (💣) to lose 3 points and end the game instantly!\n\n<b>Commands:</b>\n• /ms - Start game\n• /msclose - Force close game\n• /msrules - Show rules"
    await update.message.reply_text(text, parse_mode="HTML")

# ==========================================
# ⚙️ UNIVERSAL ENGINE (TIMER & ROUTER)
# ==========================================
def get_unified_markup(game):
    t = game['type']
    if t == 'xo': return get_xo_markup(game['board'])
    if t == 'c4': return get_c4_markup(game['board'])
    if t == 'rps': return get_rps_markup()
    if t == 'rev': return get_rev_markup(game['board'])
    if t == 'ms': return get_ms_markup(game['visible'])

async def live_countdown(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    game_key = job.data['game_key']
    chat_id = job.data['chat_id']

    if game_key not in active_games:
        safe_remove_job(job)
        return

    game = active_games[game_key]
    if game.get('is_processing'): 
        return

    game['time_left'] -= 3

    if game['time_left'] <= 0:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=game['message_id'],
                text=f"⏳ <b>Game Closed due to 60 seconds of inactivity!</b>\nType a command to start a new one.", parse_mode="HTML"
            )
        except Exception: 
            pass 
        del active_games[game_key]
        safe_remove_job(job)
    else:
        try:
            text = f"{game['base_text']}\n\n(⏳ {game['time_left']} seconds remaining)"
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=game['message_id'],
                text=text, reply_markup=get_unified_markup(game), parse_mode="HTML"
            )
        except Exception: 
            pass 

# ==========================================
# 📋 GAMES & HELP MENU
# ==========================================
async def show_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_approval(update): return
    text = (
        "🕹️ <b>AVAILABLE ARCADE GAMES</b> 🕹️\n\n"
        "Choose a game to start playing:\n\n"
        "❌ <b>Tic-Tac-Toe:</b> /xo\n"
        "🔴 <b>Connect Four:</b> /c4\n"
        "🪨 <b>Rock Paper Scissors:</b> /rps\n"
        "⚫ <b>Othello (Reversi):</b> /reversi\n"
        "💣 <b>Minesweeper Raid:</b> /ms\n\n"
        "Type the command to start! Use /ghelp to see all commands."
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_approval(update): return
    text = (
        "📖 <b>ARCADE COMMAND CENTER</b> 📖\n\n"
        "<b>Global:</b>\n"
        "• /games - List available games\n"
        "• /arcadepoints - View Top 20 Global Leaderboard\n"
        "• /ghelp - Show this command list\n\n"
        "<b>Games (Start / Rules / Close):</b>\n"
        "• Tic-Tac-Toe: /xo, /xorules, /xoclose\n"
        "• Connect 4: /c4, /c4rules, /c4close\n"
        "• RPS: /rps, /rpsrules, /rpsclose\n"
        "• Reversi: /reversi, /reversirules, /reversiclose\n"
        "• Minesweeper: /ms, /msrules, /msclose\n\n"
        "<b>Admin (Bot Owner Only):</b>\n"
        "• /approve_group &lt;group_id&gt;\n"
        "• /dismiss_group &lt;group_id&gt;\n"
        "• /addadmin &lt;userid&gt;\n"
        "• /removeadmin &lt;userid&gt;"
    )
    await update.message.reply_text(text, parse_mode="HTML")

# ==========================================
# 🎮 GAME STARTERS & CLOSERS
# ==========================================
async def start_any_game(update: Update, context: ContextTypes.DEFAULT_TYPE, game_type: str):
    chat_id = update.effective_chat.id
    user = update.effective_user
    game_key = f"{chat_id}_{game_type}"

    # Only blocks if the EXACT SAME GAME is already running in this chat
    if game_key in active_games:
        await update.message.reply_text(f"❌ This specific game is already running in this group! Finish it or type /{game_type}close.")
        return

    if game_type == 'xo':
        base_text = "🎮 <b>Tic-Tac-Toe</b>\n\n❌ Player 1: Waiting...\n⭕ Player 2: Waiting...\n\n<b>Anyone can tap to play as ❌!</b>\n📖 <i>Type /xorules for rules</i>"
        game = {'type': 'xo', 'board': [XO_EMPTY]*9, 'turn': XO_P1}
    elif game_type == 'c4':
        base_text = "🎮 <b>Connect Four</b>\n\n🔴 Player 1: Waiting...\n🟡 Player 2: Waiting...\n\n<b>Anyone can tap to play as 🔴!</b>\n📖 <i>Type /c4rules for rules</i>"
        game = {'type': 'c4', 'board': [C4_EMPTY]*42, 'turn': C4_P1}
    elif game_type == 'rps':
        base_text = "🎮 <b>Rock Paper Scissors!</b>\n\n👤 Player 1: Waiting...\n👤 Player 2: Waiting...\n\n<b>Anyone can tap to play!</b>\n📖 <i>Type /rpsrules for rules</i>"
        game = {'type': 'rps', 'p1_choice': None, 'p2_choice': None}
    elif game_type == 'rev':
        base_text = "🎮 <b>Othello (Reversi)</b>\n\n⚫ P1: Waiting... (2)\n⚪ P2: Waiting... (2)\n\n<b>Anyone can tap to play as ⚫!</b>\n📖 <i>Type /reversirules for rules</i>"
        board = init_rev_board()
        game = {'type': 'rev', 'board': board, 'turn': REV_P1, 'valid': get_rev_valid(board, REV_P1)}
    elif game_type == 'ms':
        base_text = "🎮 <b>Minesweeper Raid</b>\n\n🔴 P1: Waiting... (Score: 0)\n🔵 P2: Waiting... (Score: 0)\n\n<b>Anyone can tap to play as 🔴!</b>\n📖 <i>Type /msrules for rules</i>"
        hidden, visible = init_ms_empty()
        game = {'type': 'ms', 'hidden': hidden, 'visible': visible, 'first': True, 's_rev': 0, 'p1_s': 0, 'p2_s': 0, 'turn': 1, 'log': ""}

    game.update({
        'creator': user.id, 
        'player_1': None, 'p1_info': "Waiting...",
        'player_2': None, 'p2_info': "Waiting...",
        'time_left': 60, 'base_text': base_text, 'is_processing': False, 'message_id': None, 'timer_job': None
    })
    
    active_games[game_key] = game
    msg = await update.message.reply_text(f"{base_text}\n\n(⏳ 60s remaining)", reply_markup=get_unified_markup(game), parse_mode="HTML")
    game['message_id'] = msg.message_id
    game['timer_job'] = context.job_queue.run_repeating(live_countdown, interval=3, first=3, data={'chat_id': chat_id, 'game_key': game_key})

async def close_specific_game(update: Update, context: ContextTypes.DEFAULT_TYPE, game_type: str, game_name: str):
    chat_id = update.effective_chat.id
    user = update.effective_user
    game_key = f"{chat_id}_{game_type}"

    if game_key not in active_games:
        await update.message.reply_text(f"ℹ️ There is no active {game_name} game running right now.")
        return

    game = active_games[game_key]
    admins = load_admins()
    
    # Permission logic: Player 1, Player 2, Game Creator, Admin list, or Bot Owner
    is_p1 = game.get('player_1') and user.id == game['player_1'].id
    is_p2 = game.get('player_2') and user.id == game['player_2'].id
    is_creator = game.get('creator') == user.id
    is_admin = str(user.id) in admins or user.id == BOT_OWNER_ID

    if not (is_p1 or is_p2 or is_creator or is_admin):
        await update.message.reply_text("❌ You do not have permission to close this game. Only the players playing, the game creator, or an admin can close it.")
        return

    safe_remove_job(game.get('timer_job'))
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id, 
            message_id=game['message_id'],
            text=f"🛑 <b>{game_name} Forcefully Closed by {html.escape(user.first_name)}.</b>", 
            parse_mode="HTML"
        )
    except Exception:
        pass
        
    del active_games[game_key]
    await update.message.reply_text(f"✅ {game_name} has been closed.")

# Handlers mapped to their specific functions (Added approval check!)
async def cmd_xo(u, c): 
    if not await check_approval(u): return
    await start_any_game(u, c, 'xo')
async def cmd_c4(u, c): 
    if not await check_approval(u): return
    await start_any_game(u, c, 'c4')
async def cmd_rps(u, c): 
    if not await check_approval(u): return
    await start_any_game(u, c, 'rps')
async def cmd_rev(u, c): 
    if not await check_approval(u): return
    await start_any_game(u, c, 'rev')
async def cmd_ms(u, c): 
    if not await check_approval(u): return
    await start_any_game(u, c, 'ms')

async def cmd_xo_close(u, c): 
    if not await check_approval(u): return
    await close_specific_game(u, c, 'xo', 'Tic-Tac-Toe')
async def cmd_c4_close(u, c): 
    if not await check_approval(u): return
    await close_specific_game(u, c, 'c4', 'Connect Four')
async def cmd_rps_close(u, c): 
    if not await check_approval(u): return
    await close_specific_game(u, c, 'rps', 'Rock Paper Scissors')
async def cmd_rev_close(u, c): 
    if not await check_approval(u): return
    await close_specific_game(u, c, 'rev', 'Othello (Reversi)')
async def cmd_ms_close(u, c): 
    if not await check_approval(u): return
    await close_specific_game(u, c, 'ms', 'Minesweeper')

# ==========================================
# 🏆 GLOBAL LEADERBOARD
# ==========================================
async def arcade_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_approval(update): return
    sorted_p = sorted(user_points.items(), key=lambda x: x[1]['points'], reverse=True)[:20]
    if not sorted_p: 
        return await update.message.reply_text("📋 <b>Leaderboard is empty!</b>", parse_mode="HTML")
    
    text = "🏆 <b>ULTIMATE ARCADE LEADERBOARD</b> 🏆\n━━━━━━━━━━━━━━━━━━━━\n"
    for r, (uid, data) in enumerate(sorted_p, 1):
        medal = "🥇" if r==1 else "🥈" if r==2 else "🥉" if r==3 else "🏅"
        text += f"{medal} <b>{data['name']}</b>: {data['points']} pts\n"
        
    my_pts = user_points.get(str(update.effective_user.id), {"points": 0})["points"]
    text += f"━━━━━━━━━━━━━━━━━━━━\n👤 <b>Your Arcade Points:</b> {my_pts}"
    await update.message.reply_text(text, parse_mode="HTML")

async def arcade_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_approval(update): return
    rules = (
        "🕹️ <b>TELEGRAM ARCADE RULES</b> 🕹️\n\n"
        "<b>/xo (Tic-Tac-Toe):</b> Classic 3x3. Win = +5 pts.\n"
        "<b>/c4 (Connect 4):</b> Connect 4 in a grid. Win = +15 pts.\n"
        "<b>/rps (Rock Paper Scissors):</b> Secret choice duel. Win = +10 pts.\n"
        "<b>/reversi (Othello):</b> Trap opponent pieces to flip them. Win = +20 pts.\n"
        "<b>/ms (Minesweeper Raid):</b> Clear safe tiles (+1 pt) avoid bombs (-3 pts). Perfect Clear = +10 pts.\n\n"
        "<b>Global Commands:</b>\n"
        "• /arcadepoints - View Top 20 Global Leaderboard\n"
        "• /addadmin <id> - Add an admin (Bot Owner only)\n"
        "• /removeadmin <id> - Remove an admin (Bot Owner only)"
    )
    await update.message.reply_text(rules, parse_mode="HTML")

# ==========================================
# 🎮 UNIVERSAL MOVE HANDLER
# ==========================================
async def handle_universal_move(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.effective_chat.id
    user = update.effective_user
    data = query.data

    # Extra security: Check if group is still approved before allowing button clicks
    if update.effective_chat.type != "private" or user.id != BOT_OWNER_ID:
        approved_groups = load_approved_groups()
        if chat_id not in approved_groups:
            return await query.answer("This group is no longer approved by the bot owner!", show_alert=True)

    # Parse game type directly from the callback data prefix (e.g., 'xo_4' -> 'xo')
    game_type = data.split('_')[0]
    game_key = f"{chat_id}_{game_type}"

    if game_key not in active_games: 
        return await query.answer("Game ended!", show_alert=True)
    game = active_games[game_key]
    
    if game['is_processing']: 
        return await query.answer("⏳ Processing...", show_alert=False)
    if query.message.message_id != game['message_id']: 
        return await query.answer("Old board!", show_alert=True)

    game['is_processing'] = True
    await query.answer()

    try:
        game_over = False
        text = ""

        # --- XO LOGIC ---
        if data.startswith("xo_"):
            idx = int(data.split('_')[1])
            if game['board'][idx] != XO_EMPTY: return
            
            # Dynamic Player 1 Assignment
            if game['turn'] == XO_P1:
                if not game['player_1']: 
                    game['player_1'], game['p1_info'] = user, get_player_info(user)
                elif user.id != game['player_1'].id: 
                    return await query.answer("It's not your turn! Wait for Player 2's turn to join.", show_alert=True)
                    
            # Dynamic Player 2 Assignment
            elif game['turn'] == XO_P2:
                if not game['player_2']: 
                    if game['player_1'] and user.id == game['player_1'].id:
                        return await query.answer("You can't play against yourself! Let someone else join.", show_alert=True)
                    game['player_2'], game['p2_info'] = user, get_player_info(user)
                elif user.id != game['player_2'].id: 
                    return await query.answer("It's not your turn!", show_alert=True)
            
            game['board'][idx] = game['turn']
            if check_xo_win(game['board'], game['turn']):
                win_info = game['p1_info'] if game['turn'] == XO_P1 else game['p2_info']
                win_id = game['player_1'].id if game['turn'] == XO_P1 else game['player_2'].id
                apply_global_points(win_id, win_info, 5)
                text, game_over = f"🏆 <b>Game Over!</b>\nWinner: {win_info} (+5 pts)", True
            elif XO_EMPTY not in game['board']:
                text, game_over = "🤝 <b>Draw!</b>", True
            else:
                game['turn'] = XO_P2 if game['turn'] == XO_P1 else XO_P1
                game['base_text'] = f"🎮 <b>Tic-Tac-Toe</b>\n\n❌ P1: {game['p1_info']}\n⭕ P2: {game['p2_info']}\n\nIt is {game['turn']}'s turn!\n📖 <i>Type /xorules for rules</i>"

        # --- C4 LOGIC ---
        elif data.startswith("c4_"):
            col = int(data.split('_')[1])
            if game['board'][col] != C4_EMPTY: return
            
            if game['turn'] == C4_P1:
                if not game['player_1']: 
                    game['player_1'], game['p1_info'] = user, get_player_info(user)
                elif user.id != game['player_1'].id: 
                    return await query.answer("It's not your turn! Wait for Player 2's turn to join.", show_alert=True)
                    
            elif game['turn'] == C4_P2:
                if not game['player_2']: 
                    if game['player_1'] and user.id == game['player_1'].id:
                        return await query.answer("You can't play against yourself! Let someone else join.", show_alert=True)
                    game['player_2'], game['p2_info'] = user, get_player_info(user)
                elif user.id != game['player_2'].id: 
                    return await query.answer("It's not your turn!", show_alert=True)
            
            drop_c4_piece(game['board'], col, game['turn'])
            if check_c4_win(game['board'], game['turn']):
                win_info = game['p1_info'] if game['turn'] == C4_P1 else game['p2_info']
                win_id = game['player_1'].id if game['turn'] == C4_P1 else game['player_2'].id
                apply_global_points(win_id, win_info, 15)
                text, game_over = f"🏆 <b>Game Over!</b>\nWinner: {win_info} (+15 pts)", True
            elif C4_EMPTY not in game['board']:
                text, game_over = "🤝 <b>Draw!</b>", True
            else:
                game['turn'] = C4_P2 if game['turn'] == C4_P1 else C4_P1
                game['base_text'] = f"🎮 <b>Connect Four</b>\n\n🔴 P1: {game['p1_info']}\n🟡 P2: {game['p2_info']}\n\nIt is {game['turn']}'s turn!\n📖 <i>Type /c4rules for rules</i>"

        # --- RPS LOGIC ---
        elif data.startswith("rps_"):
            choice = data.split('_')[1]
            if not game['player_1']:
                game['player_1'], game['p1_info'], game['p1_choice'] = user, get_player_info(user), choice
            elif user.id == game['player_1'].id:
                if game['p1_choice']: return
                game['p1_choice'] = choice
            elif not game['player_2']:
                if user.id == game['player_1'].id:
                    return await query.answer("You can't play against yourself!", show_alert=True)
                game['player_2'], game['p2_info'], game['p2_choice'] = user, get_player_info(user), choice
            elif user.id == game['player_2'].id:
                if game['p2_choice']: return
                game['p2_choice'] = choice
            else:
                return await query.answer("This game is full!", show_alert=True)

            if game['p1_choice'] and game['p2_choice']:
                c1, c2 = game['p1_choice'], game['p2_choice']
                text = f"💥 <b>THE REVEAL!</b> 💥\n\n👤 {game['p1_info']}: {RPS_EMOJIS[c1]}\n👤 {game['p2_info']}: {RPS_EMOJIS[c2]}\n\n"
                if c1 == c2: 
                    text += "🤝 <b>Draw!</b>"
                else:
                    win = 1 if RPS_WINS[c1] == c2 else 2
                    win_info = game['p1_info'] if win == 1 else game['p2_info']
                    win_id = game['player_1'].id if win == 1 else game['player_2'].id
                    apply_global_points(win_id, win_info, 10)
                    text += f"🏆 <b>{win_info} wins! (+10 pts)</b>"
                game_over = True
            else:
                s1 = "✅" if game['p1_choice'] else "🤔"
                s2 = "✅" if game['p2_choice'] else "🤔"
                game['base_text'] = f"🎮 <b>RPS</b>\n\n👤 P1: {game['p1_info']} ({s1})\n👤 P2: {game['p2_info']} ({s2})\n\n📖 <i>Type /rpsrules for rules</i>"

        # --- REVERSI LOGIC ---
        elif data.startswith("rev_"):
            idx = int(data.split('_')[1])
            
            if game['turn'] == REV_P1:
                if not game['player_1']: 
                    game['player_1'], game['p1_info'] = user, get_player_info(user)
                elif user.id != game['player_1'].id: 
                    return await query.answer("It's not your turn! Wait for Player 2's turn to join.", show_alert=True)
                    
            elif game['turn'] == REV_P2:
                if not game['player_2']: 
                    if game['player_1'] and user.id == game['player_1'].id:
                        return await query.answer("You can't play against yourself! Let someone else join.", show_alert=True)
                    game['player_2'], game['p2_info'] = user, get_player_info(user)
                elif user.id != game['player_2'].id: 
                    return await query.answer("It's not your turn!", show_alert=True)
                    
            if idx not in game['valid']: return
            
            flips = get_rev_flips(game['board'], idx//6, idx%6, game['turn'])
            game['board'][idx] = game['turn']
            for f in flips: 
                game['board'][f] = game['turn']
            
            next_turn = REV_P2 if game['turn'] == REV_P1 else REV_P1
            next_moves = get_rev_valid(game['board'], next_turn)
            skipped = ""
            
            if not next_moves:
                curr_moves = get_rev_valid(game['board'], game['turn'])
                if not curr_moves:
                    b, w = count_pieces(game['board'])
                    if b > w:
                        apply_global_points(game['player_1'].id, game['p1_info'], 20)
                        text, game_over = f"🏆 <b>Game Over!</b>\n⚫ {b} | ⚪ {w}\nWinner: {game['p1_info']} (+20 pts)", True
                    elif w > b:
                        apply_global_points(game['player_2'].id, game['p2_info'], 20)
                        text, game_over = f"🏆 <b>Game Over!</b>\n⚫ {b} | ⚪ {w}\nWinner: {game['p2_info']} (+20 pts)", True
                    else: 
                        text, game_over = f"🤝 <b>Tie!</b>\n⚫ {b} | ⚪ {w}", True
                else:
                    skipped = f"\n\n⚠️ {next_turn} skipped!"
                    game['valid'] = curr_moves
            else:
                game['turn'], game['valid'] = next_turn, next_moves

            if not game_over:
                b, w = count_pieces(game['board'])
                game['base_text'] = f"🎮 <b>Reversi</b>\n\n⚫ P1: {game['p1_info']} ({b})\n⚪ P2: {game['p2_info']} ({w})\n\n{game['turn']}'s turn!{skipped}\n📖 <i>Type /reversirules for rules</i>"

        # --- MINESWEEPER LOGIC ---
        elif data.startswith("ms_"):
            idx = int(data.split('_')[1])
            if game['visible'][idx] != MS_HIDDEN: return
            
            if game['turn'] == 1:
                if not game['player_1']: 
                    game['player_1'], game['p1_info'] = user, get_player_info(user)
                elif user.id != game['player_1'].id: 
                    return await query.answer("It's not your turn! Wait for Player 2's turn to join.", show_alert=True)
                    
            elif game['turn'] == 2:
                if not game['player_2']: 
                    if game['player_1'] and user.id == game['player_1'].id:
                        return await query.answer("You can't play against yourself! Let someone else join.", show_alert=True)
                    game['player_2'], game['p2_info'] = user, get_player_info(user)
                elif user.id != game['player_2'].id: 
                    return await query.answer("It's not your turn!", show_alert=True)
            
            if game['first']:
                game['hidden'], game['first'] = generate_ms_board(idx), False
                
            pts = reveal_ms_cell(game['hidden'], game['visible'], idx)
            icon = "🔴" if game['turn'] == 1 else "🔵"
            
            if pts == -1:
                game['log'] = f"💥 BOOM! {icon} hit a mine! (-3)"
                if game['turn'] == 1: 
                    game['p1_s'] -= 3
                    apply_global_points(game['player_1'].id, game['p1_info'], -3)
                else: 
                    game['p2_s'] -= 3
                    apply_global_points(game['player_2'].id, game['p2_info'], -3)
                for i in range(64):
                    if game['hidden'][i] == 'M': game['visible'][i] = MS_MINE
                win_text = f"🏆 {game['p1_info']} wins!" if game['p1_s'] > game['p2_s'] else f"🏆 {game['p2_info']} wins!" if game['p2_s'] > game['p1_s'] else "🤝 Tie!"
                text, game_over = f"💥 <b>MINE HIT!</b> 💥\n🔴 {game['p1_info']}: {game['p1_s']}\n🔵 {game['p2_info']}: {game['p2_s']}\n\n{win_text}", True
            else:
                game['s_rev'] += pts
                game['log'] = f"✅ {icon} cleared {pts} tiles! (+{pts})"
                if game['turn'] == 1: 
                    game['p1_s'] += pts
                    apply_global_points(game['player_1'].id, game['p1_info'], pts)
                else: 
                    game['p2_s'] += pts
                    apply_global_points(game['player_2'].id, game['p2_info'], pts)
                
                if game['s_rev'] >= 54: # 64 - 10 mines
                    for i in range(64):
                        if game['hidden'][i] == 'M': game['visible'][i] = MS_MINE
                    win_text = ""
                    if game['p1_s'] > game['p2_s']: 
                        apply_global_points(game['player_1'].id, game['p1_info'], 10)
                        win_text = f"🏆 {game['p1_info']} wins! (+10 Bonus)"
                    elif game['p2_s'] > game['p1_s']: 
                        apply_global_points(game['player_2'].id, game['p2_info'], 10)
                        win_text = f"🏆 {game['p2_info']} wins! (+10 Bonus)"
                    else: 
                        win_text = "🤝 Tie!"
                    text, game_over = f"✨ <b>PERFECT CLEAR!</b> ✨\n🔴 {game['p1_info']}: {game['p1_s']}\n🔵 {game['p2_info']}: {game['p2_s']}\n\n{win_text}", True
                else:
                    game['turn'] = 2 if game['turn'] == 1 else 1
                    game['base_text'] = f"🎮 <b>Minesweeper</b>\n\n🔴 P1: {game['p1_info']} ({game['p1_s']})\n🔵 P2: {game['p2_info']} ({game['p2_s']})\n\n{game['log']}\nTurn: {'🔴' if game['turn']==1 else '🔵'}\n📖 <i>Type /msrules for rules</i>"


        # --- EXECUTE UI UPDATE ---
        if game_over:
            safe_remove_job(game.get('timer_job'))
            markup = None if game['type'] == 'rps' else get_unified_markup(game)
            for _ in range(3):
                try:
                    await context.bot.edit_message_text(chat_id=chat_id, message_id=game['message_id'], text=text, reply_markup=markup, parse_mode="HTML")
                    break
                except Exception: 
                    await asyncio.sleep(0.5)
            del active_games[game_key]
        else:
            game['time_left'] = 60
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id, message_id=game['message_id'],
                    text=f"{game['base_text']}\n\n(⏳ 60 seconds remaining)", reply_markup=get_unified_markup(game), parse_mode="HTML"
                )
            except Exception: 
                pass

    except Exception as e: 
        print(f"Error: {e}")
    finally:
        if game_key in active_games: 
            active_games[game_key]['is_processing'] = False

# ==========================================
# 🚀 MAIN RUNNER
# ==========================================
if __name__ == '__main__':
    app = Application.builder().token(BOT_TOKEN).build()

    # Approval Management
    app.add_handler(CommandHandler("approve_group", approve_group))
    app.add_handler(CommandHandler("dismiss_group", dismiss_group))

    # Admin Tools
    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(CommandHandler("removeadmin", remove_admin))
    app.add_handler(CommandHandler("arcadepoints", arcade_leaderboard))

    # Game Starters
    app.add_handler(CommandHandler("xo", cmd_xo))
    app.add_handler(CommandHandler("c4", cmd_c4))
    app.add_handler(CommandHandler("rps", cmd_rps))
    app.add_handler(CommandHandler("reversi", cmd_rev))
    app.add_handler(CommandHandler("ms", cmd_ms))

    # Game Closers
    app.add_handler(CommandHandler("xoclose", cmd_xo_close))
    app.add_handler(CommandHandler("c4close", cmd_c4_close))
    app.add_handler(CommandHandler("rpsclose", cmd_rps_close))
    app.add_handler(CommandHandler("reversiclose", cmd_rev_close))
    app.add_handler(CommandHandler("msclose", cmd_ms_close))

    # Game Rules
    app.add_handler(CommandHandler("xorules", cmd_xo_rules))
    app.add_handler(CommandHandler("c4rules", cmd_c4_rules))
    app.add_handler(CommandHandler("rpsrules", cmd_rps_rules))
    app.add_handler(CommandHandler("reversirules", cmd_rev_rules))
    app.add_handler(CommandHandler("msrules", cmd_ms_rules))

    # Arcade Help & Info
    app.add_handler(CommandHandler("games", show_games))
    app.add_handler(CommandHandler("ghelp", show_help))
    
    # Universal Move Router
    app.add_handler(CallbackQueryHandler(handle_universal_move))

    print("🚀 Ultimate Telegram Arcade with Strict Group Approval is running!")
    app.run_polling()
