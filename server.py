"""
Serveur Web & API Backend pour SitePulse AI SaaS.
100% Python Standard Library (aucune installation requise).
Fournit l'API d'audit en temps réel et sert l'interface utilisateur.
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from audit_engine import run_audit

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PORT = int(os.environ.get("PORT", 8080))
CLIENTS_FILE = "clients.json"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class SaaSHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            return super().do_GET()
        elif parsed.path == "/api/clients":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            clients_data = {"clients": []}
            if os.path.exists(CLIENTS_FILE):
                try:
                    with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
                        clients_data = json.load(f)
                except Exception:
                    pass
            self.wfile.write(json.dumps(clients_data, ensure_ascii=False).encode("utf-8"))
        else:
            return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == "/api/audit":
            # API d'audit en temps réel
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            
            try:
                payload = json.loads(post_data)
                url = payload.get("url", "").strip()
            except Exception:
                url = ""

            if not url:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "URL manquante"}).encode("utf-8"))
                return

            print(f"[API BACKEND] Requête d'audit reçue pour : {url}")
            audit_result = run_audit(url)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(audit_result, ensure_ascii=False).encode("utf-8"))
            
        elif parsed.path == "/api/clients":
            # Ajout d'un nouveau client sous surveillance
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            
            try:
                new_client = json.loads(post_data)
            except Exception:
                new_client = {}
                
            clients_data = {"settings": {}, "clients": []}
            if os.path.exists(CLIENTS_FILE):
                try:
                    with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
                        clients_data = json.load(f)
                except Exception:
                    pass
                    
            if new_client.get("url"):
                new_client["id"] = f"client_{len(clients_data.get('clients', [])) + 1:02d}"
                new_client["active"] = True
                clients_data.setdefault("clients", []).append(new_client)
                
                with open(CLIENTS_FILE, "w", encoding="utf-8") as f:
                    json.dump(clients_data, f, ensure_ascii=False, indent=2)
                    
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "clients": clients_data.get("clients", [])}, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, SaaSHandler)
    print(f"======================================================")
    print(f"🚀 BACKEND & FRONTEND DÉMARRÉS AVEC SUCCÈS")
    print(f"🌐 Accédez à votre SaaS sur : http://localhost:{PORT}")
    print(f"======================================================")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
