"""
Module d'envoi d'e-mails pour SitePulse AI.
100% Python Standard Library.
Gère la génération des e-mails HTML professionnels et l'expédition via Resend API, SMTP ou boîte d'envoi locale.
"""

import os
import sys
import json
import smtplib
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

CONFIG_FILE = "config.json"
OUTBOX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "emails_outbox")

def get_email_config():
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f).get("email_settings", {})
        except Exception:
            pass
    return {
        "provider": "outbox", # "resend", "smtp" ou "outbox"
        "from_email": "SitePulse AI <alerts@sitepulse-ai.com>",
        "resend_api_key": os.environ.get("RESEND_API_KEY", ""),
        "smtp_host": os.environ.get("SMTP_HOST", ""),
        "smtp_port": int(os.environ.get("SMTP_PORT", 587)),
        "smtp_user": os.environ.get("SMTP_USER", ""),
        "smtp_pass": os.environ.get("SMTP_PASS", "")
    }

def generate_email_html(client_name, site_url, audit_data):
    score = audit_data.get("score", 0)
    badge_color = "#10b981" if score >= 80 else ("#f59e0b" if score >= 50 else "#ef4444")
    badge_label = "🟢 Excellent" if score >= 80 else ("🟡 Moyen" if score >= 50 else "🔴 Critique")
    
    metrics = audit_data.get("metrics", {})
    response_time = audit_data.get("response_time_ms", 0)
    status_code = audit_data.get("status_code", 200)
    cms = metrics.get("cms_detected", "Non détecté")
    
    alerts_html = ""
    for a in audit_data.get("alertes", []):
        alerts_html += f"<li style='margin-bottom:8px; color:#f87171;'>⚠️ {a}</li>"
    if not alerts_html:
        alerts_html = "<li style='color:#34d399;'>✅ Aucune anomalie détectée cette nuit ! Tout fonctionne à merveille.</li>"

    recs_html = ""
    for i, r in enumerate(audit_data.get("recommandations", []), 1):
        recs_html += f"<li style='margin-bottom:8px; color:#cbd5e1;'><strong>{i}.</strong> {r}</li>"
    if not recs_html:
        recs_html = "<li style='color:#cbd5e1;'>Votre site respecte toutes les bonnes pratiques SEO et sécurité.</li>"

    date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Rapport Quotidien de Surveillance</title>
</head>
<body style="background-color:#0b0f19; font-family:'Helvetica Neue', Helvetica, Arial, sans-serif; color:#f8fafc; margin:0; padding:30px 15px;">
  <div style="max-width:600px; margin:0 auto; background-color:#141e33; border:1px solid #232f48; border-radius:16px; overflow:hidden;">
    
    <!-- Header -->
    <div style="background:linear-gradient(135deg, #4f46e5, #7c3aed); padding:24px 30px; text-align:center;">
      <h1 style="color:#ffffff; margin:0; font-size:24px; font-weight:800; letter-spacing:-0.5px;">⚡ SitePulse AI</h1>
      <p style="color:#e0e7ff; margin:4px 0 0; font-size:13px;">Rapport d'inspection nocturne automatisé</p>
    </div>

    <!-- Body -->
    <div style="padding:30px;">
      <p style="font-size:16px; color:#cbd5e1; margin-top:0;">Bonjour <strong>{client_name}</strong>,</p>
      <p style="font-size:14px; color:#94a3b8; line-height:1.6;">
        Notre robot a inspecté votre site web <strong>{site_url}</strong> cette nuit à minuit. Voici le bilan de santé technique :
      </p>

      <!-- Score Card -->
      <div style="background:#090d16; border:1px solid #232f48; border-radius:12px; padding:20px; text-align:center; margin:24px 0;">
        <div style="font-size:12px; text-transform:uppercase; color:#94a3b8; letter-spacing:1px; font-weight:700;">Score Global de Santé</div>
        <div style="font-size:48px; font-weight:800; color:{badge_color}; line-height:1.2; margin:6px 0;">{score} <span style="font-size:20px; color:#64748b;">/ 100</span></div>
        <div style="display:inline-block; background:rgba(255,255,255,0.08); padding:4px 12px; border-radius:20px; font-size:13px; font-weight:600; color:#fff;">
          {badge_label}
        </div>
      </div>

      <!-- Quick Metrics -->
      <table style="width:100%; border-collapse:collapse; margin-bottom:24px; font-size:14px;">
        <tr style="border-bottom:1px solid #232f48;">
          <td style="padding:10px 0; color:#94a3b8;">Temps de réponse serveur</td>
          <td style="padding:10px 0; text-align:right; font-weight:700; color:#fff;">{response_time} ms</td>
        </tr>
        <tr style="border-bottom:1px solid #232f48;">
          <td style="padding:10px 0; color:#94a3b8;">Statut d'accessibilité</td>
          <td style="padding:10px 0; text-align:right; font-weight:700; color:#34d399;">HTTP {status_code} (Opérationnel)</td>
        </tr>
        <tr style="border-bottom:1px solid #232f48;">
          <td style="padding:10px 0; color:#94a3b8;">Technologie détectée</td>
          <td style="padding:10px 0; text-align:right; font-weight:700; color:#818cf8;">{cms}</td>
        </tr>
      </table>

      <!-- Alerts -->
      <div style="margin-bottom:24px;">
        <h3 style="font-size:15px; color:#f8fafc; margin-bottom:10px;">Points d'attention :</h3>
        <ul style="padding-left:20px; margin:0; font-size:13.5px; line-height:1.6;">
          {alerts_html}
        </ul>
      </div>

      <!-- Plan d'action -->
      <div style="margin-bottom:30px;">
        <h3 style="font-size:15px; color:#f8fafc; margin-bottom:10px;">Actions prioritaires recommandées :</h3>
        <ul style="padding-left:20px; margin:0; font-size:13.5px; line-height:1.6;">
          {recs_html}
        </ul>
      </div>

      <!-- CTA -->
      <div style="text-align:center;">
        <a href="https://sitepulse-saas.onrender.com" style="display:inline-block; background:#4f46e5; color:#ffffff; text-decoration:none; padding:14px 28px; font-weight:700; border-radius:10px; font-size:14px;">
          Accéder à mon Espace Client
        </a>
      </div>

    </div>

    <!-- Footer -->
    <div style="background:#090d16; padding:18px 30px; text-align:center; border-top:1px solid #232f48; font-size:12px; color:#64748b;">
      Rapport généré le {date_str} par votre service SitePulse AI.<br>
      © 2026 SitePulse AI — Tous droits réservés.
    </div>

  </div>
</body>
</html>"""
    return html

def send_audit_email(client_email, client_name, site_url, audit_data):
    if not client_email:
        return False, "E-mail destinataire manquant"

    cfg = get_email_config()
    subject = f"⚡ Rapport de Santé Quotidien ({audit_data.get('score', 0)}/100) — {site_url}"
    html_content = generate_email_html(client_name, site_url, audit_data)
    
    # 1. Option Resend API
    if cfg.get("resend_api_key"):
        try:
            req_data = json.dumps({
                "from": cfg.get("from_email", "alerts@sitepulse-ai.com"),
                "to": [client_email],
                "subject": subject,
                "html": html_content
            }).encode("utf-8")
            
            req = urllib.request.Request(
                "https://api.resend.com/emails",
                data=req_data,
                headers={
                    "Authorization": f"Bearer {cfg['resend_api_key']}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 201):
                    print(f"[MAILER] E-mail envoyé avec succès via Resend à {client_email}")
                    return True, "Envoyé via Resend"
        except Exception as e:
            print(f"[MAILER ERROR] Resend échoué : {e}")

    # 2. Option SMTP
    if cfg.get("smtp_host") and cfg.get("smtp_user"):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = cfg.get("from_email", "alerts@sitepulse-ai.com")
            msg["To"] = client_email
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"], timeout=10) as server:
                server.starttls()
                server.login(cfg["smtp_user"], cfg["smtp_pass"])
                server.sendmail(msg["From"], [client_email], msg.as_string())
            print(f"[MAILER] E-mail envoyé avec succès via SMTP à {client_email}")
            return True, "Envoyé via SMTP"
        except Exception as e:
            print(f"[MAILER ERROR] SMTP échoué : {e}")

    # 3. Fallback : Sauvegarde dans Outbox (Simulation sans échec)
    os.makedirs(OUTBOX_DIR, exist_ok=True)
    slug = client_email.replace("@", "_at_").replace(".", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(OUTBOX_DIR, f"email_{slug}_{timestamp}.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"[MAILER] E-mail sauvegardé dans la boîte d'envoi locale : {file_path}")
    return True, f"Sauvegardé dans Outbox : {file_path}"

if __name__ == "__main__":
    demo_audit = {
        "score": 95,
        "url": "https://example.com",
        "response_time_ms": 710,
        "status_code": 200,
        "metrics": {"cms_detected": "WordPress"},
        "alertes": ["En-tête X-Frame-Options manquant"],
        "recommandations": ["Configurer l'en-tête de sécurité X-Frame-Options."]
    }
    send_audit_email("client@test.fr", "Client Test", "https://example.com", demo_audit)
