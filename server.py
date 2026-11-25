"""
Serveur Web & API Backend pour SitePulse AI SaaS — Version 2 (Espace Membre & Multi-Comptes).
100% Python Standard Library.
Gère l'authentification (sessions sécurisées), l'espace client privé et les audits en direct.
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from audit_engine import run_audit
from mailer import send_audit_email
import db
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PORT = int(os.environ.get("PORT", 8080))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Seuls ces fichiers sont accessibles publiquement (tout le reste = 404)
PUBLIC_FILES = {"/", "/index.html", "/manifest.json", "/success.html"}

# Limiteur de requêtes simple (par adresse IP)
_HITS = {}

def too_many_requests(key, limit, window_seconds):
    now = time.time()
    recent = [t for t in _HITS.get(key, []) if now - t < window_seconds]
    if len(recent) >= limit:
        _HITS[key] = recent
        return True
    recent.append(now)
    _HITS[key] = recent
    return False

class SaaSHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def send_head(self):
        # Sécurité : on ne sert que les fichiers publics (pas la base de données, ni le code)
        path = urllib.parse.urlparse(self.path).path
        if path not in PUBLIC_FILES:
            self.send_error(404, "Not found")
            return None
        return super().send_head()

    def _client_ip(self):
        forwarded = self.headers.get("X-Forwarded-For", "")
        return forwarded.split(",")[0].strip() if forwarded else self.client_address[0]

    def _rate_limited(self, name, limit, window_seconds):
        if too_many_requests(f"{name}:{self._client_ip()}", limit, window_seconds):
            self._send_json({"success": False, "error": "Trop de tentatives. Réessaie plus tard."}, 429)
            return True
        return False

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _get_auth_user(self):
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            return db.get_user_from_token(token), token
        return None, None

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            return super().do_GET()
            
        elif path == "/api/me":
            user, _ = self._get_auth_user()
            if not user:
                return self._send_json({"authenticated": False}, 401)
            return self._send_json({"authenticated": True, "user": user})

        elif path == "/api/my-sites":
            user, _ = self._get_auth_user()
            if not user:
                return self._send_json({"error": "Non authentifié"}, 401)
            is_admin = (user["role"] == "admin")
            sites = db.get_user_sites(user["id"], is_admin=is_admin)
            return self._send_json({"sites": sites, "is_admin": is_admin})

        elif path == "/api/config":
            cfg_path = os.path.join(BASE_DIR, "config.json")
            cfg_data = {}
            if os.path.exists(cfg_path):
                try:
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        cfg_data = json.load(f)
                except Exception:
                    pass
            # Renvoyer les liens de paiement publics
            return self._send_json({
                "stripe": cfg_data.get("stripe_settings", {}),
                "general": cfg_data.get("general", {})
            })

        elif path == "/api/clients":
            # Compatibilité V1 — réservé aux utilisateurs connectés
            user, _ = self._get_auth_user()
            if not user:
                return self._send_json({"error": "Non authentifié"}, 401)
            sites = db.get_user_sites(user["id"], is_admin=(user["role"] == "admin"))
            return self._send_json({"clients": sites})

        else:
            return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()

        # Inscription
        if path == "/api/register":
            if self._rate_limited("register", 10, 3600):
                return
            name = body.get("name", "").strip()
            email = body.get("email", "").strip()
            password = body.get("password", "").strip()

            if not name or not email or not password:
                return self._send_json({"success": False, "error": "Tous les champs sont requis."}, 400)

            auth_res, err = db.register_user(name, email, password)
            if err:
                return self._send_json({"success": False, "error": err}, 400)
            return self._send_json({"success": True, **auth_res})

        # Connexion
        elif path == "/api/login":
            if self._rate_limited("login", 10, 300):
                return
            email = body.get("email", "").strip()
            password = body.get("password", "").strip()

            auth_res, err = db.login_user(email, password)
            if err:
                return self._send_json({"success": False, "error": err}, 401)
            return self._send_json({"success": True, **auth_res})

        # Déconnexion
        elif path == "/api/logout":
            _, token = self._get_auth_user()
            if token:
                db.logout_user(token)
            return self._send_json({"success": True})

        # Audit en direct
        elif path == "/api/audit":
            if self._rate_limited("audit", 30, 3600):
                return
            url = body.get("url", "").strip()
            if not url:
                return self._send_json({"success": False, "error": "URL manquante"}, 400)
            audit_result = run_audit(url)
            return self._send_json(audit_result)

        # Ajouter un site à son compte
        elif path == "/api/my-sites":
            user, _ = self._get_auth_user()
            if not user:
                return self._send_json({"error": "Connexion requise pour sauvegarder un site"}, 401)
                
            site_name = body.get("name", "Mon Site").strip()
            site_url = body.get("url", "").strip()
            if not site_url:
                return self._send_json({"error": "URL requise"}, 400)
                
            site_id = db.add_user_site(user["id"], site_name, site_url)
            return self._send_json({"success": True, "site_id": site_id})

        # Tester l'envoi d'e-mail de rapport
        elif path == "/api/send-test-email":
            if self._rate_limited("email", 5, 3600):
                return
            dest_email = body.get("email", "").strip()
            site_url = body.get("url", "https://example.com").strip()
            audit_data = body.get("audit_data")
            if not audit_data:
                audit_data = run_audit(site_url)
            ok, msg = send_audit_email(dest_email, "Client Test", site_url, audit_data)
            return self._send_json({"success": ok, "message": msg})

        else:
            return self._send_json({"error": "Route introuvable"}, 404)

def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, SaaSHandler)
    print(f"======================================================")
    print(f"🚀 VERSION 2 DÉMARRÉE (Auth + Espace Membre + SQLite)")
    print(f"🌐 Accédez à votre SaaS sur : http://localhost:{PORT}")
    print(f"🔑 Compte Fondateur (Admin) : admin@sitepulse.ai (mot de passe = variable ADMIN_PASSWORD)")
    print(f"======================================================")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
