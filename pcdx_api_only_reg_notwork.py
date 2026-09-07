import sqlite3
import json
import random
import string
import os
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)
DB_FILE = "pharmacom.db"

# Increase payload limit for high-quality chat images
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB limit

def connect_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_now_ist():
    return (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")

def generate_random_uid(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def add_score(userid, points, reason):
    try:
        with connect_db() as conn:
            # Update user's total score
            conn.execute("UPDATE users SET score = score + ? WHERE userid=?", (points, userid))
            # Log the transaction in history
            conn.execute("INSERT INTO score_history (userid, points, reason, timestamp) VALUES (?,?,?,?)",
                         (userid, points, reason, get_now_ist()))
            
            # Referral Bonus Logic: Referrer gets 10% of what their referrals earn
            user = conn.execute("SELECT referred_by FROM users WHERE userid=?", (userid,)).fetchone()
            if user and user['referred_by']:
                bonus = max(1, int(points * 0.1))
                referrer = conn.execute("SELECT userid FROM users WHERE referral_code=?", (user['referred_by'],)).fetchone()
                if referrer:
                    conn.execute("UPDATE users SET score = score + ? WHERE userid=?", (bonus, referrer['userid']))
                    conn.execute("INSERT INTO score_history (userid, points, reason, timestamp) VALUES (?,?,?,?)",
                                 (referrer['userid'], bonus, f"Referral Bonus from {userid}", get_now_ist()))
    except Exception as e:
        print(f"Error adding score: {e}")

def init_db():
    with connect_db() as conn:
        # Create Core Tables
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            userid TEXT PRIMARY KEY, name TEXT, email TEXT, password TEXT, 
            shop_name TEXT, role TEXT, shop_type TEXT, phone TEXT, 
            city TEXT, status TEXT DEFAULT 'pending', score INTEGER DEFAULT 0,
            expiry_date TIMESTAMP, referral_code TEXT, referred_by TEXT,
            profile_img TEXT, license_img TEXT, reference_name TEXT)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS score_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, userid TEXT, points INTEGER, 
            reason TEXT, timestamp TIMESTAMP)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS companies (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, dosage_form TEXT, packaging TEXT, company_name TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS stokists (id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER, name TEXT, type TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS stokist_master (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, area TEXT, UNIQUE(name, area))''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, userid TEXT, type TEXT, req_action TEXT DEFAULT 'add', 
            name TEXT, dosage_form TEXT, packaging TEXT, company TEXT, stokist_list TEXT, 
            status TEXT DEFAULT 'pending', created_at TIMESTAMP, action_at TIMESTAMP, action_by TEXT)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS discussion (
            id INTEGER PRIMARY KEY AUTOINCREMENT, userid TEXT, user_name TEXT, message TEXT, 
            image_url TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT, userid TEXT, type TEXT, message TEXT, 
            score_rewarded INTEGER, is_read INTEGER DEFAULT 0)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS special_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, days INTEGER, is_used INTEGER DEFAULT 0)''')

        # DYNAMIC MIGRATIONS: Add columns if they are missing from existing DB
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        cols = [c[1] for c in cursor.fetchall()]
        if 'score' not in cols: conn.execute("ALTER TABLE users ADD COLUMN score INTEGER DEFAULT 0")

        cursor.execute("PRAGMA table_info(requests)")
        cols = [c[1] for c in cursor.fetchall()]
        if 'req_action' not in cols: conn.execute("ALTER TABLE requests ADD COLUMN req_action TEXT DEFAULT 'add'")
            
    print("Database Initialized Successfully.")

# --- USER & PROFILE ROUTES ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    uid = data.get('email')
    try:
        with connect_db() as conn:
            user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            status = 'approved' if user_count == 0 else 'pending'
            role = 'admin' if user_count == 0 else 'Owner'
            expiry = (datetime.utcnow() + timedelta(hours=5, minutes=30, days=180 if user_count == 0 else 7)).strftime("%Y-%m-%d")
            ref_code = f"PCDX-{generate_random_uid()}"
            referred_by = data.get('referred_by', '')
            
            # Explicitly define columns to match the actual database schema
            # Adjust the column names below to match exactly what is in your DB
            query = '''INSERT INTO users (userid, name, email, password, shop_name, role, shop_type, phone, city, status, expiry_date, referral_code, referred_by, score) 
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
            
            values = (uid, data['name'], uid, data['password'], data['shop_name'], role, 
                      data['shop_type'], data['phone'], data['city'], status, expiry, 
                      ref_code, referred_by, 0)
            
            conn.execute(query, values)
            
            if referred_by:
                add_score(uid, 50, "Registration Welcome Bonus (Referral)")
            return jsonify({"status": "success", "referral_code": ref_code}), 200
    except Exception as e: 
        # Log the actual error on the server side to debug faster
        print(f"Error: {e}") 
        return jsonify({"error": str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    with connect_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE userid=? AND password=?", (data['userid'], data['password'])).fetchone()
        if user:
            if user['status'] == 'deleted': return jsonify({"error": "Account Deleted"}), 403
            if user['status'] != 'approved': return jsonify({"error": "Pending Approval"}), 401
            add_score(user['userid'], 5, "Daily Activity Reward")
            exp_dt = datetime.strptime(user['expiry_date'], "%Y-%m-%d")
            return jsonify({
                "status": "success", "userid": user['userid'], "name": user['name'], "shop_name": user['shop_name'],
                "role": user['role'], "expiry": user['expiry_date'], 
                "is_expired": exp_dt < (datetime.utcnow() + timedelta(hours=5, minutes=30))
            }), 200
    return jsonify({"error": "Invalid credentials"}), 400

@app.route('/api/get_user_profile', methods=['GET'])
def get_profile():
    with connect_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE userid=?", (request.args.get('userid'),)).fetchone()
        if user:
            refs = conn.execute("SELECT name, shop_name, score FROM users WHERE referred_by=?", (user['referral_code'],)).fetchall()
            d = dict(user)
            d['referral_list'] = [dict(r) for r in refs]
            return jsonify(d)
    return jsonify({"error": "Not found"}), 404

# --- PRODUCT & COMPANY DATA ROUTES ---

@app.route('/api/get_data', methods=['GET'])
def get_data():
    uid, mode = request.args.get('userid'), request.args.get('mode', 'company')
    with connect_db() as conn:
        user = conn.execute("SELECT role, score, expiry_date FROM users WHERE userid=?", (uid,)).fetchone()
        if not user: return jsonify({"error": "User not found"}), 404
        table = "companies" if mode == "company" else "products"
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        exp_dt = datetime.strptime(user['expiry_date'], "%Y-%m-%d")
        return jsonify({
            "score": user['score'], "role": user['role'], "expiry_date": user['expiry_date'], 
            "is_expired": exp_dt < (datetime.utcnow() + timedelta(hours=5, minutes=30)), 
            "items": [dict(row) for row in rows]
        })

@app.route('/api/get_stokists', methods=['GET'])
def get_stokists():
    with connect_db() as conn:
        rows = conn.execute("SELECT name FROM stokists WHERE item_id=? AND type=?", (request.args.get('id'), request.args.get('mode'))).fetchall()
        return jsonify([r['name'] for r in rows])

@app.route('/api/get_all_stokists', methods=['GET'])
def get_all_stokists():
    with connect_db() as conn:
        return jsonify([f"{r['name']} ({r['area']})" for r in conn.execute("SELECT name, area FROM stokist_master ORDER BY name ASC").fetchall()])

# --- REQUESTS & SUBMISSIONS ---

@app.route('/api/add_request', methods=['POST'])
def add_request():
    data = request.json
    with connect_db() as conn:
        conn.execute("INSERT INTO requests (userid, type, req_action, name, dosage_form, packaging, company, stokist_list, created_at) VALUES (?,?,?,?,?,?,?,?,?)", 
                     (data['userid'], data['type'], data.get('req_action', 'add'), data['name'], data.get('dosage_form',''), data.get('packaging',''), data.get('company',''), json.dumps(data.get('stokists', [])), get_now_ist()))
        add_score(data['userid'], 10, f"Submitted {data['type']} request")
    return jsonify({"status": "ok"})

@app.route('/api/get_user_requests', methods=['GET'])
def get_user_requests():
    with connect_db() as conn:
        return jsonify([dict(r) for r in conn.execute("SELECT * FROM requests WHERE userid=? ORDER BY created_at DESC", (request.args.get('userid'),)).fetchall()])

# --- DISCUSSION (CHAT) ROUTES ---

@app.route('/api/get_messages', methods=['GET'])
def get_messages():
    with connect_db() as conn:
        rows = conn.execute("SELECT * FROM discussion ORDER BY timestamp DESC LIMIT 100").fetchall()
        return jsonify([dict(r) for r in reversed(rows)])

@app.route('/api/send_message', methods=['POST'])
def send_message():
    data = request.json
    with connect_db() as conn:
        conn.execute("INSERT INTO discussion (userid, user_name, message, image_url, timestamp) VALUES (?,?,?,?,?)", 
                     (data['userid'], data['user_name'], data['message'], data.get('image_url',''), get_now_ist()))
        add_score(data['userid'], 2, "Chat Activity Bonus")
    return jsonify({"status": "ok"})

# --- UTILITY ROUTES ---

@app.route('/api/get_score_history', methods=['GET'])
def get_score_history():
    with connect_db() as conn:
        rows = conn.execute("SELECT * FROM score_history WHERE userid=? ORDER BY timestamp DESC", (request.args.get('userid'),)).fetchall()
        return jsonify([dict(r) for r in rows])

@app.route('/api/redeem_code', methods=['POST'])
def redeem_code():
    data = request.json
    uid, code = data.get('userid'), data.get('code')
    with connect_db() as conn:
        special = conn.execute("SELECT * FROM special_codes WHERE code=? AND is_used=0", (code,)).fetchone()
        if special:
            user = conn.execute("SELECT expiry_date FROM users WHERE userid=?", (uid,)).fetchone()
            if user:
                curr_exp = datetime.strptime(user['expiry_date'], "%Y-%m-%d")
                new_exp = (max(curr_exp, datetime.utcnow() + timedelta(hours=5, minutes=30)) + timedelta(days=special['days'])).strftime("%Y-%m-%d")
                conn.execute("UPDATE users SET expiry_date=? WHERE userid=?", (new_exp, uid))
                conn.execute("UPDATE special_codes SET is_used=1 WHERE id=?", (special['id'],))
                return jsonify({"status": "success", "new_expiry": new_exp})
    return jsonify({"error": "Invalid or used code"}), 400

@app.route('/api/check_updates', methods=['GET'])
def check_updates():
    uid = request.args.get('userid')
    with connect_db() as conn:
        rows = conn.execute("SELECT * FROM updates WHERE userid=? AND is_read=0", (uid,)).fetchall()
        updates = [dict(r) for r in rows]
        conn.execute("UPDATE updates SET is_read=1 WHERE userid=? AND is_read=0", (uid,))
        return jsonify(updates)

# --- ADMIN ROUTES ---

@app.route('/api/admin/pending_users', methods=['GET'])
def pending_users():
    with connect_db() as conn:
        return jsonify([dict(r) for r in conn.execute("SELECT * FROM users WHERE status='pending'").fetchall()])

@app.route('/api/admin/all_users', methods=['GET'])
def admin_all_users():
    with connect_db() as conn:
        return jsonify([dict(r) for r in conn.execute("SELECT * FROM users WHERE status!='deleted' AND status!='pending'").fetchall()])

@app.route('/api/admin/deleted_users', methods=['GET'])
def get_deleted():
    with connect_db() as conn:
        return jsonify([dict(r) for r in conn.execute("SELECT * FROM users WHERE status='deleted'").fetchall()])

@app.route('/api/admin/approve_user', methods=['POST'])
def approve_user():
    expiry = (datetime.utcnow() + timedelta(hours=5, minutes=30, days=180)).strftime("%Y-%m-%d")
    with connect_db() as conn:
        conn.execute("UPDATE users SET status='approved', expiry_date=? WHERE userid=?", (expiry, request.json['userid']))
    return jsonify({"status": "ok"})

@app.route('/api/admin/delete_user', methods=['POST'])
def delete_user_admin():
    with connect_db() as conn:
        conn.execute("UPDATE users SET status='deleted' WHERE referral_code=?", (request.json['uid'],))
    return jsonify({"status": "ok"})

@app.route('/api/admin/update_expiry', methods=['POST'])
def update_expiry():
    data = request.json
    uid, days = data.get('uid'), int(data.get('days', 0))
    with connect_db() as conn:
        if uid == "ALL":
            for u in conn.execute("SELECT userid, expiry_date FROM users").fetchall():
                new_exp = (max(datetime.strptime(u['expiry_date'], "%Y-%m-%d"), datetime.utcnow()) + timedelta(days=days)).strftime("%Y-%m-%d")
                conn.execute("UPDATE users SET expiry_date=? WHERE userid=?", (new_exp, u['userid']))
        else:
            user = conn.execute("SELECT userid, expiry_date FROM users WHERE referral_code=?", (uid,)).fetchone()
            if user:
                new_exp = (max(datetime.strptime(user['expiry_date'], "%Y-%m-%d"), datetime.utcnow()) + timedelta(days=days)).strftime("%Y-%m-%d")
                conn.execute("UPDATE users SET expiry_date=? WHERE userid=?", (new_exp, user['userid']))
    return jsonify({"status": "ok"})

@app.route('/api/admin/pending_requests', methods=['GET'])
def admin_reqs():
    with connect_db() as conn:
        return jsonify([dict(r) for r in conn.execute("SELECT * FROM requests WHERE status='pending'").fetchall()])

@app.route('/api/admin/request_history', methods=['GET'])
def get_admin_history():
    with connect_db() as conn:
        return jsonify([dict(r) for r in conn.execute("SELECT * FROM requests WHERE status!='pending' ORDER BY action_at DESC").fetchall()])

@app.route('/api/admin/approve_request', methods=['POST'])
def admin_approve_req():
    data = request.json
    rid, action, aid = data['request_id'], data['action'], data.get('admin_id', 'admin')
    with connect_db() as conn:
        now = get_now_ist()
        if action == 'deny':
            conn.execute("UPDATE requests SET status='denied', action_at=?, action_by=? WHERE id=?", (now, aid, rid))
            req = conn.execute("SELECT userid, name FROM requests WHERE id=?", (rid,)).fetchone()
            if req: conn.execute("INSERT INTO updates (userid, type, message, score_rewarded) VALUES (?,?,?,?)", 
                             (req['userid'], 'request_denied', f"Your request for {req['name']} was denied.", 0))
        else:
            req = conn.execute("SELECT * FROM requests WHERE id=?", (rid,)).fetchone()
            if req:
                table = "companies" if req['type'] == 'company' else "products"
                if req['req_action'] == 'remove_stokist':
                    item = conn.execute(f"SELECT id FROM {table} WHERE name=?", (req['name'],)).fetchone()
                    if item:
                        for s in json.loads(req['stokist_list']): 
                            conn.execute("DELETE FROM stokists WHERE item_id=? AND name=? AND type=?", (item['id'], s, req['type']))
                elif req['req_action'] == 'remove': 
                    conn.execute(f"DELETE FROM {table} WHERE name=?", (req['name'],))
                else: # ADD logic
                    if req['type'] == 'company':
                        conn.execute("INSERT OR IGNORE INTO companies (name) VALUES (?)", (req['name'],))
                        iid = conn.execute("SELECT id FROM companies WHERE name=?", (req['name'],)).fetchone()[0]
                    else:
                        conn.execute("INSERT INTO products (name, dosage_form, packaging, company_name) VALUES (?,?,?,?)", (req['name'], req['dosage_form'], req['packaging'], req['company']))
                        iid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                    for s in json.loads(req['stokist_list']): 
                        conn.execute("INSERT OR IGNORE INTO stokists (item_id, name, type) VALUES (?,?,?)", (iid, s, req['type']))
                
                conn.execute("UPDATE requests SET status='approved', action_at=?, action_by=? WHERE id=?", (now, aid, rid))
                add_score(req['userid'], 20, f"Request Approved: {req['name']}")
                conn.execute("INSERT INTO updates (userid, type, message, score_rewarded) VALUES (?,?,?,?)", 
                             (req['userid'], 'request_approved', f"Your request for {req['name']} was approved!", 20))
    return jsonify({"status": "ok"})

@app.route('/api/admin/add_special_code', methods=['POST'])
def add_special_code():
    data = request.json
    with connect_db() as conn:
        conn.execute("INSERT INTO special_codes (code, days) VALUES (?,?)", (data['code'], data['days']))
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5050)