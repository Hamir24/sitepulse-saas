"""
Base de données SQLite & Système d'Authentification pour SitePulse AI.
100% Python Standard Library (sqlite3 + hashlib + secrets).
Gère les comptes utilisateurs, les sessions, les sites surveillés et l'historique d'audit.
"""

import sqlite3
import hashlib
import hmac
import secrets
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sitepulse.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

PBKDF2_ITERATIONS = 200_000

def hash_password(password, salt=None):
    """Hash sécurisé (PBKDF2-SHA256, 200 000 itérations) — 100% bibliothèque standard."""
    if not salt:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS)
    return f"pbkdf2${PBKDF2_ITERATIONS}${salt}${dk.hex()}"

def is_modern_hash(stored_hash):
    return stored_hash.startswith("pbkdf2$")

def verify_password(password, stored_hash):
    try:
        if is_modern_hash(stored_hash):
            _, iterations, salt, hashed = stored_hash.split("$")
            dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations))
            return hmac.compare_digest(dk.hex(), hashed)
        # Ancien format (sha256 + sel) : encore accepté, puis converti à la connexion
        salt, hashed = stored_hash.split("$", 1)
        test_hash = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
        return hmac.compare_digest(test_hash, hashed)
    except Exception:
        return False

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Table Utilisateurs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'client', -- 'admin' ou 'client'
                plan TEXT DEFAULT 'Pro (49€/mois)',
                created_at TEXT NOT NULL
            )
        """)
        
        # Table Sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Table Sites surveillés
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Table Historique des Audits
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                score INTEGER NOT NULL,
                status_code INTEGER,
                response_time_ms INTEGER,
                data_json TEXT,
                FOREIGN KEY (site_id) REFERENCES sites (id)
            )
        """)
        
        # --- Compte Fondateur (Admin) ---
        # Le mot de passe vient de la variable d'environnement ADMIN_PASSWORD.
        # Sans variable, un mot de passe aléatoire est généré et affiché UNE fois dans la console.
        env_pwd = os.environ.get("ADMIN_PASSWORD", "").strip()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("SELECT id, password_hash FROM users WHERE email = 'admin@sitepulse.ai'")
        admin = cursor.fetchone()

        if not admin:
            pwd = env_pwd or secrets.token_urlsafe(12)
            cursor.execute("""
                INSERT INTO users (name, email, password_hash, role, plan, created_at)
                VALUES ('Fondateur (Admin)', 'admin@sitepulse.ai', ?, 'admin', 'Fondateur Unlimited', ?)
            """, (hash_password(pwd), now))
            admin_id = cursor.lastrowid
            if not env_pwd:
                print(f"🔑 Compte admin créé : admin@sitepulse.ai / {pwd}  (note-le, il ne sera plus affiché)")

            # Ajouter 2 sites exemples sous l'admin
            cursor.execute("""
                INSERT INTO sites (user_id, name, url, active, created_at)
                VALUES (?, 'Boutique Mode Démo', 'https://example.com', 1, ?)
            """, (admin_id, now))
            cursor.execute("""
                INSERT INTO sites (user_id, name, url, active, created_at)
                VALUES (?, 'Portail Tech Python', 'https://www.python.org', 1, ?)
            """, (admin_id, now))
        elif env_pwd:
            # ADMIN_PASSWORD défini : on (re)met ce mot de passe à chaque démarrage
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(env_pwd), admin["id"]))
        elif verify_password("admin123", admin["password_hash"]):
            # Ancien mot de passe par défaut détecté : on le remplace tout de suite
            pwd = secrets.token_urlsafe(12)
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(pwd), admin["id"]))
            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (admin["id"],))
            print(f"🔑 Ancien mot de passe 'admin123' remplacé. Nouveau : admin@sitepulse.ai / {pwd}")

        conn.commit()

# --- Fonctions Utilisateurs & Auth ---

def register_user(name, email, password):
    email = email.strip().lower()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return None, "Cet e-mail est déjà utilisé."
            
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pwd_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role, plan, created_at)
            VALUES (?, ?, ?, 'client', 'Pro (49€/mois)', ?)
        """, (name, email, pwd_hash, now))
        conn.commit()
        user_id = cursor.lastrowid
        
    return login_user(email, password)

def login_user(email, password):
    email = email.strip().lower()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, password_hash, role, plan FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if not user or not verify_password(password, user["password_hash"]):
            return None, "Identifiants invalides."

        # Conversion automatique des anciens hash vers PBKDF2
        if not is_modern_hash(user["password_hash"]):
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(password), user["id"]))

        token = secrets.token_hex(24)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)", (token, user["id"], now))
        conn.commit()
        
        return {
            "token": token,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "plan": user["plan"]
            }
        }, None

def get_user_from_token(token):
    if not token:
        return None
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.name, u.email, u.role, u.plan
            FROM users u
            JOIN sessions s ON u.id = s.user_id
            WHERE s.token = ?
        """, (token,))
        user = cursor.fetchone()
        if user:
            return dict(user)
    return None

def logout_user(token):
    if not token:
        return
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()

# --- Fonctions Sites & Audits ---

def get_user_sites(user_id, is_admin=False):
    with get_db() as conn:
        cursor = conn.cursor()
        if is_admin:
            cursor.execute("""
                SELECT s.id, s.name, s.url, s.active, s.created_at, u.name as owner_name, u.email as owner_email
                FROM sites s
                JOIN users u ON s.user_id = u.id
                ORDER BY s.id DESC
            """)
        else:
            cursor.execute("""
                SELECT id, name, url, active, created_at
                FROM sites
                WHERE user_id = ?
                ORDER BY id DESC
            """, (user_id,))
        return [dict(r) for r in cursor.fetchall()]

def add_user_site(user_id, name, url):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sites (user_id, name, url, active, created_at)
            VALUES (?, ?, ?, 1, ?)
        """, (user_id, name, url, now))
        conn.commit()
        return cursor.lastrowid

def save_audit_result(site_id, audit_data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audits (site_id, date, score, status_code, response_time_ms, data_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            site_id,
            now,
            audit_data.get("score", 0),
            audit_data.get("status_code", 0),
            audit_data.get("response_time_ms", 0),
            json.dumps(audit_data, ensure_ascii=False)
        ))
        conn.commit()

# Initialisation automatique au chargement
init_db()
