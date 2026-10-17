"""
Batch Audit Runner - Exécute la tournée d'inspection nocturne pour l'ensemble des clients du SaaS.
Produit un rapport individuel pour chaque client et un Master Digest pour le fondateur.
"""

import os
import sys
import json
from datetime import datetime
from audit_engine import run_audit, generate_markdown_report
from mailer import send_audit_email

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CLIENTS_FILE = "clients.json"
REPORTS_DIR = "reports"

def run_all():
    if not os.path.exists(CLIENTS_FILE):
        print(f"[!] Fichier {CLIENTS_FILE} introuvable.")
        return

    with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    settings = data.get("settings", {})
    clients = [c for c in data.get("clients", []) if c.get("active", True)]
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    print(f"=== {settings.get('saas_name', 'SaaS Audit')} ===")
    print(f"[*] Tournée d'inspection lancée le {timestamp}")
    print(f"[*] Nombre de sites clients sous surveillance : {len(clients)}\n")
    
    results = []
    
    for client in clients:
        cid = client.get("id", "client")
        cname = client.get("name", "Client")
        url = client.get("url")
        print(f"-> Analyse de [{cname}] ({url})...")
        
        audit_res = run_audit(url)
        audit_res["client_name"] = cname
        audit_res["client_email"] = client.get("email")
        audit_res["client_plan"] = client.get("plan")
        results.append(audit_res)
        
        # Rapport individuel client
        client_dir = os.path.join(REPORTS_DIR, cid)
        os.makedirs(client_dir, exist_ok=True)
        report_path = os.path.join(client_dir, f"audit_{today_str}.md")
        json_path = os.path.join(client_dir, f"audit_{today_str}.json")
        
        md_text = generate_markdown_report(audit_res)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(md_text)
            
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(audit_res, f, ensure_ascii=False, indent=2)
            
        score = audit_res.get("score", 0)
        badge = "🟢" if score >= 80 else ("🟡" if score >= 50 else "🔴")
        print(f"   {badge} Score : {score}/100 | Rapport généré : {report_path}")

        # Envoi automatique de l'e-mail au client
        c_email = client.get("email")
        if c_email:
            send_audit_email(c_email, cname, url, audit_res)

    # Génération du Master Digest pour le fondateur
    digest = []
    digest.append(f"# 🛡️ Master Digest Quotidien — {settings.get('saas_name')}")
    digest.append(f"**Date :** `{timestamp}` | **Sites surveillés :** `{len(clients)}`\n")
    
    scores = [r.get("score", 0) for r in results if r.get("success")]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    
    digest.append(f"### 📊 Synthèse Globale du Portefeuille")
    digest.append(f"- **Score de santé moyen :** `{avg_score} / 100`")
    digest.append(f"- **Sites opérationnels (HTTP 200) :** `{sum(1 for r in results if r.get('status_code') == 200)} / {len(results)}`")
    digest.append(f"- **Sites nécessitant une intervention urgente (Score < 60) :** `{sum(1 for r in results if r.get('score', 0) < 60)}`\n")
    
    digest.append("### 📋 Tableau de bord des clients")
    digest.append("| Client | URL | Score | Vitesse | Statut | Alertes critiques |")
    digest.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    
    for r in results:
        sc = r.get("score", 0)
        sc_badge = "🟢" if sc >= 80 else ("🟡" if sc >= 50 else "🔴")
        speed = f"{r.get('response_time_ms', 0)} ms"
        status = r.get("status_code", "ERR")
        alerts_count = len(r.get("alertes", []))
        digest.append(f"| **{r.get('client_name')}** | [{r.get('url')}]({r.get('url')}) | {sc_badge} `{sc}/100` | `{speed}` | `{status}` | `{alerts_count}` alertes |")
        
    digest.append("\n---\n*Ce digest est destiné exclusivement au fondateur du SaaS pour piloter les alertes clients.*")
    
    master_path = os.path.join(REPORTS_DIR, f"master_digest_{today_str}.md")
    with open(master_path, "w", encoding="utf-8") as f:
        f.write("\n".join(digest))
        
    print(f"\n[+] Master Digest généré avec succès : {master_path}")
    return master_path

if __name__ == "__main__":
    run_all()
