import sqlite3
import json
import random
import string
import os
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)
DB_FILE = "pharmacom.db"

# Critical for images: Increase limit to 64MB for high-res verification photos
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024 

def connect_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_now_ist():
    # IST is UTC+5:30
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
            
            # Referral Bonus: Referrer gets 10% of what their referrals earn
            user = conn.execute("SELECT referred_by FROM users WHERE userid=?", (userid,)).fetchone()
            if user and user['referred_by']:
                bonus = max(1, int(points * 0.1))
                referrer = conn.execute("SELECT userid FROM users WHERE referral_code=?", (user['referred_by'],)).fetchone()
                if referrer:
                    conn.execute("UPDATE users SET score = score + ? WHERE userid=?", (bonus, referrer['userid']))
                    conn.execute("INSERT INTO score_history (userid, points, reason, timestamp) VALUES (?,?,?,?)",
                                 (referrer['userid'], bonus, f"Referral Bonus from {userid}", get_now_ist()))
    except Exception as e:
        print(f"Score Error: {e}")

def init_db():
    with connect_db() as conn:
        # Core Tables
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
            id INTEGER PRIMARY KEY AUTOINCREMENT, userid TEXT, message TEXT, 
            image_url TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT, userid TEXT, type TEXT, message TEXT, 
            score_rewarded INTEGER, is_read INTEGER DEFAULT 0)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS special_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, days INTEGER, is_used INTEGER DEFAULT 0)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS system_config (key TEXT PRIMARY KEY, value TEXT)''')
        conn.execute("INSERT OR IGNORE INTO system_config (key, value) VALUES ('free_slots', '10')")

        # Migrations
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        cols = [c[1] for c in cursor.fetchall()]
        needed = ['score', 'profile_img', 'license_img', 'reference_name', 'shop_type', 'referral_code', 'referred_by']
        for col in needed:
            if col not in cols:
                conn.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
                if col == 'score': conn.execute("UPDATE users SET score = 0 WHERE score IS NULL")

    print("Database Initialized Successfully.")

# --- USER ROUTES ---

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
            
            conn.execute('''INSERT INTO users (userid, name, email, password, shop_name, role, shop_type, phone, city, status, expiry_date, referral_code, referred_by, profile_img, license_img, reference_name, score) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                         (uid, data.get('name'), uid, data.get('password'), data.get('shop_name'), role, data.get('shop_type'), data.get('phone'), data.get('city'), status, expiry, ref_code, data.get('referred_by', ''), data.get('profile_img',''), data.get('license_img',''), data.get('reference_name',''), 0))
            
            if data.get('referred_by'): add_score(uid, 50, "Registration Welcome Bonus")
            return jsonify({"status": "success", "referral_code": ref_code}), 200
    except Exception as e: return jsonify({"error": str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    with connect_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE userid=? AND password=?", (data['userid'], data['password'])).fetchone()
        if user:
            if user['status'] == 'deleted': return jsonify({"error": "Account Deleted"}), 403
            if user['status'] != 'approved': return jsonify({"error": "Pending Approval"}), 401
            add_score(user['userid'], 5, "Daily Activity Bonus")
            return jsonify({"status": "success", "userid": user['userid'], "name": user['name'], "shop_name": user['shop_name'], "role": user['role'], "expiry": user['expiry_date']})
    return jsonify({"error": "Invalid credentials"}), 400

@app.route('/api/get_user_profile', methods=['GET'])
def get_profile():
    with connect_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE userid=?", (request.args.get('userid'),)).fetchone()
        if user:
            refs = conn.execute("SELECT name, shop_name, score FROM users WHERE referred_by=?", (user['referral_code'],)).fetchall()
            d = dict(user); d['referral_list'] = [dict(r) for r in refs]
            return jsonify(d)
    return jsonify({"error": "Not found"}), 404

@app.route('/api/delete_account', methods=['GET'])
def delete_account():
    with connect_db() as conn: 
        conn.execute("UPDATE users SET status='deleted' WHERE userid=?", (request.args.get('userid'),))
    return jsonify({"status": "ok"})

# --- DATA ROUTES ---

@app.route('/api/get_data', methods=['GET'])
def get_data():
    uid, mode = request.args.get('userid'), request.args.get('mode', 'company')
    with connect_db() as conn:
        user = conn.execute("SELECT role, score, expiry_date FROM users WHERE userid=?", (uid,)).fetchone()
        if not user: return jsonify({"error": "User not found"}), 404
        
        # FILTER: Automatically hide items with 0 stokists
        if mode == 'company':
            query = "SELECT c.* FROM companies c WHERE EXISTS (SELECT 1 FROM stokists s WHERE s.item_id = c.id AND s.type = 'company')"
        else: # product
            query = "SELECT p.* FROM products p WHERE EXISTS (SELECT 1 FROM stokists s WHERE s.item_id = p.id AND s.type = 'product')"
            
        rows = conn.execute(query).fetchall()
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

# --- REQUEST ROUTES ---

@app.route('/api/add_request', methods=['POST'])
def add_request():
    data = request.json
    with connect_db() as conn:
        conn.execute("INSERT INTO requests (userid, type, req_action, name, dosage_form, packaging, company, stokist_list, created_at) VALUES (?,?,?,?,?,?,?,?,?)", 
                     (data['userid'], data['type'], data.get('req_action', 'add'), data['name'], data.get('dosage_form',''), data.get('packaging',''), data.get('company',''), json.dumps(data.get('stokists', [])), get_now_ist()))
        add_score(data['userid'], 10, f"Submitted {data['type']} contribution")
    return jsonify({"status": "ok"})

@app.route('/api/get_user_requests', methods=['GET'])
def get_user_requests():
    with connect_db() as conn:
        return jsonify([dict(r) for r in conn.execute("SELECT * FROM requests WHERE userid=? ORDER BY created_at DESC", (request.args.get('userid'),)).fetchall()])

# --- CHAT ROUTES ---

@app.route('/api/get_messages', methods=['GET'])
def get_messages():
    with connect_db() as conn:
        # Username@Shop format
        query = "SELECT d.*, u.name as u_name, u.shop_name as s_name FROM discussion d JOIN users u ON d.userid = u.userid ORDER BY d.timestamp DESC LIMIT 100"
        rows = conn.execute(query).fetchall()
        messages = []
        for r in reversed(rows):
            d = dict(r)
            d['user_name'] = f"{r['u_name']}@{r['s_name']}"
            try:
                dt = datetime.strptime(r['timestamp'], "%Y-%m-%d %H:%M:%S")
                d['time'] = dt.strftime("%I:%M %p")
            except:
                d['time'] = r['timestamp']
            messages.append(d)
        return jsonify(messages)

@app.route('/api/send_message', methods=['POST'])
def send_message():
    data = request.json
    with connect_db() as conn:
        conn.execute("INSERT INTO discussion (userid, message, image_url, timestamp) VALUES (?,?,?,?)", 
                     (data['userid'], data['message'], data.get('image_url',''), get_now_ist()))
        add_score(data['userid'], 2, "Chat Participation")
    return jsonify({"status": "ok"})

# --- UTILITY ROUTES ---

@app.route('/api/get_score_history', methods=['GET'])
def get_score_history():
    with connect_db() as conn:
        return jsonify([dict(r) for r in conn.execute("SELECT * FROM score_history WHERE userid=? ORDER BY timestamp DESC", (request.args.get('userid'),)).fetchall()])

@app.route('/api/check_update', methods=['GET'])
def check_update():
    return jsonify({
        "version_code": 7, 
        "server_url": "http://165.227.201.31:5050/api/", 
        "apk_url": "http://165.227.201.31:5050/static/app-release.apk"
    }), 200
    
@app.route('/api/redeem_code', methods=['POST'])
def redeem():
    data = request.json
    with connect_db() as conn:
        special = conn.execute("SELECT * FROM special_codes WHERE code=? AND is_used=0", (data['code'],)).fetchone()
        if special:
            user = conn.execute("SELECT expiry_date FROM users WHERE userid=?", (data['userid'],)).fetchone()
            new_exp = (max(datetime.strptime(user['expiry_date'], "%Y-%m-%d"), datetime.utcnow()) + timedelta(days=special['days'])).strftime("%Y-%m-%d")
            conn.execute("UPDATE users SET expiry_date=? WHERE userid=?", (new_exp, data['userid']))
            conn.execute("UPDATE special_codes SET is_used=1 WHERE id=?", (special['id'],))
            return jsonify({"status": "success", "new_expiry": new_exp})
    return jsonify({"error": "Invalid or Used Code"}), 400

# --- ADMIN ROUTES ---

@app.route('/api/admin/pending_users', methods=['GET'])
@app.route('/api/admin/all_users', methods=['GET'])
@app.route('/api/admin/deleted_users', methods=['GET'])
def admin_users_list():
    if 'pending_users' in request.path: status_filter = "status='pending'"
    elif 'deleted_users' in request.path: status_filter = "status='deleted'"
    else: status_filter = "status!='deleted' AND status!='pending'"
    with connect_db() as conn:
        return jsonify([dict(r) for r in conn.execute(f"SELECT *, referral_code as uid FROM users WHERE {status_filter}").fetchall()])

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
@app.route('/api/admin/request_history', methods=['GET'])
def admin_requests_list():
    status_filter = "r.status='pending'" if 'pending' in request.path else "r.status!='pending'"
    with connect_db() as conn:
        # Join with users to get user_fullname
        query = f"SELECT r.*, u.name as user_fullname FROM requests r JOIN users u ON r.userid = u.userid WHERE {status_filter} ORDER BY r.created_at DESC"
        return jsonify([dict(r) for r in conn.execute(query).fetchall()])

@app.route('/api/admin/approve_request', methods=['POST'])
def admin_approve_req():
    data = request.json
    rid, action = data['request_id'], data['action']
    with connect_db() as conn:
        now = get_now_ist()
        if action == 'deny':
            conn.execute("UPDATE requests SET status='denied', action_at=? WHERE id=?", (now, rid))
        else:
            req = conn.execute("SELECT * FROM requests WHERE id=?", (rid,)).fetchone()
            if req:
                table = "companies" if req['type'] == 'company' else "products"
                if req['req_action'] == 'remove':
                    # CASCADE DELETE Logic
                    item = conn.execute(f"SELECT id FROM {table} WHERE name=?", (req['name'],)).fetchone()
                    if item:
                        conn.execute(f"DELETE FROM stokists WHERE item_id=? AND type=?", (item['id'], req['type']))
                        if req['type'] == 'company': conn.execute("DELETE FROM products WHERE company_name=?", (req['name'],))
                        conn.execute(f"DELETE FROM {table} WHERE id=?", (item['id'],))
                elif req['req_action'] == 'remove_stokist':
                    item = conn.execute(f"SELECT id FROM {table} WHERE name=?", (req['name'],)).fetchone()
                    if item:
                        for s in json.loads(req['stokist_list']): 
                            conn.execute("DELETE FROM stokists WHERE item_id=? AND name=? AND type=?", (item['id'], s, req['type']))
                else: # ADD
                    if req['type'] == 'company':
                        conn.execute("INSERT OR IGNORE INTO companies (name) VALUES (?)", (req['name'],))
                        iid = conn.execute("SELECT id FROM companies WHERE name=?", (req['name'],)).fetchone()[0]
                    else:
                        conn.execute("INSERT INTO products (name, dosage_form, packaging, company_name) VALUES (?,?,?,?)", (req['name'], req['dosage_form'], req['packaging'], req['company']))
                        iid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                    for s in json.loads(req['stokist_list']): conn.execute("INSERT OR IGNORE INTO stokists (item_id, name, type) VALUES (?,?,?)", (iid, s, req['type']))
                
                conn.execute("UPDATE requests SET status='approved', action_at=? WHERE id=?", (now, rid))
                add_score(req['userid'], 20, f"Approved: {req['name']}")
    return jsonify({"status": "ok"})

@app.route('/api/admin/system_config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'POST':
        with connect_db() as conn:
            for k, v in request.json.items(): conn.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES (?,?)", (k, str(v)))
        return jsonify({"status": "ok"})
    with connect_db() as conn:
        return jsonify({r['key']: r['value'] for r in conn.execute("SELECT * FROM system_config").fetchall()})

@app.route('/api/admin/add_special_code', methods=['POST'])
def add_special_code():
    with connect_db() as conn:
        conn.execute("INSERT INTO special_codes (code, days) VALUES (?,?)", (request.json['code'], request.json['days']))
    return jsonify({"status": "ok"})

@app.route('/api/admin/list_special_codes', methods=['GET'])
def list_codes():
    with connect_db() as conn:
        return jsonify([dict(r) for r in conn.execute("SELECT * FROM special_codes ORDER BY id DESC").fetchall()])

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5050)