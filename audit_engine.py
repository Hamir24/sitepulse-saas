"""
Audit Engine - Moteur d'audit automatique de santé et SEO de sites web.
Conçu pour fonctionner de manière autonome sans dépendances externes lourdes (100% Python Standard Library).
"""

import sys
import os
import json
import time
import ssl
import urllib.request
import urllib.parse
import gzip
from html.parser import HTMLParser
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

class PageParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.title = ""
        self.in_title = False
        self.meta_tags = []
        self.headings = {"h1": [], "h2": [], "h3": []}
        self.current_heading = None
        self.images = []
        self.links = []
        
    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        tag_lower = tag.lower()
        
        if tag_lower == 'title':
            self.in_title = True
        elif tag_lower == 'meta':
            self.meta_tags.append(attr_dict)
        elif tag_lower in self.headings:
            self.current_heading = tag_lower
        elif tag_lower == 'img':
            src = attr_dict.get('src', '')
            alt = attr_dict.get('alt', None)
            self.images.append({'src': src, 'alt': alt})
        elif tag_lower == 'a':
            href = attr_dict.get('href', '')
            if href:
                full_url = urllib.parse.urljoin(self.base_url, href)
                self.links.append({'url': full_url, 'text': ''})
                
    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower == 'title':
            self.in_title = False
        elif tag_lower in self.headings:
            self.current_heading = None
            
    def handle_data(self, data):
        if self.in_title:
            self.title += data.strip()
        elif self.current_heading:
            text = data.strip()
            if text:
                self.headings[self.current_heading].append(text)

def run_audit(target_url):
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url
        
    print(f"[*] Démarrage de l'audit pour : {target_url}")
    audit_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 AuditSaaSBot/1.0'
    }
    
    start_time = time.time()
    req = urllib.request.Request(target_url, headers=headers)
    
    context = ssl.create_default_context()
    
    try:
        with urllib.request.urlopen(req, timeout=15, context=context) as response:
            final_url = response.geturl()
            response_time_ms = round((time.time() - start_time) * 1000)
            status_code = response.getcode()
            content_type = response.headers.get('Content-Type', '')
            content_encoding = response.headers.get('Content-Encoding', '').lower()
            charset = 'utf-8'
            if 'charset=' in content_type:
                charset = content_type.split('charset=')[-1].split(';')[0].strip()
            
            raw_bytes = response.read()
            if 'gzip' in content_encoding or (len(raw_bytes) > 2 and raw_bytes[:2] == b'\x1f\x8b'):
                try:
                    raw_bytes = gzip.decompress(raw_bytes)
                except Exception:
                    pass

            # En-têtes de sécurité HTTP
            sec_headers = {
                "hsts": bool(response.headers.get('Strict-Transport-Security')),
                "x_frame_options": response.headers.get('X-Frame-Options', ''),
                "x_content_type_options": response.headers.get('X-Content-Type-Options', ''),
                "server": response.headers.get('Server', '')
            }
            raw_html = raw_bytes.decode(charset, errors='replace')
            target_url = final_url
    except Exception as e:
        return {
            "success": False,
            "url": target_url,
            "error": str(e),
            "date": audit_date
        }
        
    # Détection de CMS / Framework
    cms_detected = "Sur-mesure (Custom)"
    html_lower = raw_html.lower()
    if "wp-content" in html_lower or "wp-includes" in html_lower or 'content="wordpress' in html_lower:
        cms_detected = "WordPress"
    elif "cdn.shopify.com" in html_lower or "window.shopify" in html_lower:
        cms_detected = "Shopify"
    elif "assets.website-files.com" in html_lower or "data-wf-page" in html_lower:
        cms_detected = "Webflow"
    elif "static.wixstatic.com" in html_lower or "wix.com" in html_lower:
        cms_detected = "Wix"
    elif "__next_data__" in html_lower:
        cms_detected = "Next.js (React)"
    elif "prestashop" in html_lower:
        cms_detected = "PrestaShop"
        
    # Analyse HTML
    parser = PageParser(target_url)
    try:
        parser.feed(raw_html)
    except Exception:
        pass
        
    # Extraction des métadonnées clés
    meta_desc = ""
    meta_viewport = ""
    meta_robots = ""
    og_title = ""
    og_image = ""
    
    for m in parser.meta_tags:
        name = m.get('name', '').lower()
        prop = m.get('property', '').lower()
        content = m.get('content', '')
        
        if name == 'description':
            meta_desc = content
        elif name == 'viewport':
            meta_viewport = content
        elif name == 'robots':
            meta_robots = content
        elif prop == 'og:title':
            og_title = content
        elif prop == 'og:image':
            og_image = content

    # Évaluation et scoring (sur 100)
    score = 100
    points_forts = []
    alertes = []
    recommandations = []
    
    # 1. Performance / Temps de réponse
    if response_time_ms < 600:
        points_forts.append(f"Temps de réponse serveur excellent ({response_time_ms} ms)")
    elif response_time_ms < 1500:
        points_forts.append(f"Temps de réponse acceptable ({response_time_ms} ms)")
    else:
        score -= 15
        alertes.append(f"Temps de réponse lent ({response_time_ms} ms > 1500 ms)")
        recommandations.append("Optimiser le serveur d'hébergement, la mise en cache (CDN) ou la taille de la page.")

    # 2. Sécurité HTTPS
    if target_url.startswith("https://"):
        points_forts.append("Connexion sécurisée par certificat SSL (HTTPS activé)")
    else:
        score -= 25
        alertes.append("Le site n'utilise pas le protocole HTTPS sécurisé")
        recommandations.append("Activer immédiatement un certificat SSL Let's Encrypt gratuit pour sécuriser les échanges.")

    # 3. Balise Titre
    title = parser.title
    if not title:
        score -= 20
        alertes.append("Balise <title> manquante")
        recommandations.append("Ajouter un titre unique et descriptif entre 30 et 60 caractères.")
    elif len(title) < 20:
        score -= 5
        alertes.append(f"Titre trop court ({len(title)} caractères) : « {title} »")
        recommandations.append("Enrichir la balise titre avec les mots-clés stratégiques de votre activité.")
    elif len(title) > 65:
        score -= 5
        alertes.append(f"Titre trop long ({len(title)} caractères), risque de tronquage sur Google")
        recommandations.append("Raccourcir le titre sous la barre des 60-65 caractères.")
    else:
        points_forts.append(f"Balise <title> optimale ({len(title)} caractères) : « {title} »")

    # 4. Meta Description
    if not meta_desc:
        score -= 15
        alertes.append("Meta description absente")
        recommandations.append("Rédiger une meta description percutante entre 120 et 155 caractères pour inciter au clic.")
    elif len(meta_desc) < 50:
        score -= 5
        alertes.append(f"Meta description courte ({len(meta_desc)} car.)")
        recommandations.append("Développer la description pour mieux résumer l'offre aux utilisateurs.")
    elif len(meta_desc) > 165:
        score -= 5
        alertes.append(f"Meta description trop longue ({len(meta_desc)} car.)")
        recommandations.append("Réduire à moins de 160 caractères pour éviter d'être coupée dans les résultats Google.")
    else:
        points_forts.append(f"Meta description présente et bien calibrée ({len(meta_desc)} caractères)")

    # 5. Mobile & Viewport
    if meta_viewport:
        points_forts.append("Balise meta viewport présente (adaptation mobile active)")
    else:
        score -= 15
        alertes.append("Balise viewport manquante (le site n'est probablement pas optimisé pour smartphones)")
        recommandations.append("Ajouter <meta name='viewport' content='width=device-width, initial-scale=1'>.")

    # 6. Structure des titres H1
    h1_count = len(parser.headings['h1'])
    if h1_count == 1:
        points_forts.append(f"Structure H1 parfaite (1 titre principal unique : « {parser.headings['h1'][0]} »)")
    elif h1_count == 0:
        score -= 10
        alertes.append("Aucun titre principal <h1> trouvé sur la page")
        recommandations.append("Définir exactement un titre <h1> décrivant la proposition de valeur principale.")
    else:
        score -= 5
        alertes.append(f"Multiples titres <h1> détectés ({h1_count} balises H1)")
        recommandations.append("Conserver un seul <h1> principal par page et hiérarchiser les autres en <h2> et <h3>.")

    # 7. Images et balises ALT
    total_imgs = len(parser.images)
    missing_alt = sum(1 for img in parser.images if not img.get('alt'))
    if total_imgs > 0:
        if missing_alt == 0:
            points_forts.append(f"Accessibilité exemplaire : les {total_imgs} images ont toutes une balise descriptive (alt)")
        else:
            score -= min(10, missing_alt * 2)
            alertes.append(f"{missing_alt} image(s) sur {total_imgs} n'ont pas d'attribut 'alt'")
            recommandations.append("Renseigner le texte alternatif (alt) pour chaque image pour booster le référencement naturel.")
    else:
        points_forts.append("Aucune image détectée sur la page d'accueil.")

    # 8. Réseaux sociaux (Open Graph)
    if og_title and og_image:
        points_forts.append("Balises Open Graph configurées (partage optimal sur LinkedIn, Twitter, Facebook)")
    else:
        alertes.append("Balises Open Graph incomplètes (aperçu réduit lors des partages sur les réseaux)")
        recommandations.append("Ajouter og:title, og:description et og:image pour maximiser les clics sur les réseaux sociaux.")

    # 9. En-têtes de sécurité HTTP
    if sec_headers.get("hsts"):
        points_forts.append("Protection HSTS active (navigation HTTPS renforcée contre l'interception)")
    if sec_headers.get("x_frame_options"):
        points_forts.append("En-tête X-Frame-Options présent (protection anti-clickjacking)")
    else:
        alertes.append("En-tête de sécurité X-Frame-Options non configuré")
        recommandations.append("Ajouter l'en-tête X-Frame-Options: SAMEORIGIN pour empêcher l'intégration non autorisée de votre site en iframe.")

    score = max(0, min(100, score))
    
    return {
        "success": True,
        "url": target_url,
        "date": audit_date,
        "status_code": status_code,
        "response_time_ms": response_time_ms,
        "score": score,
        "metrics": {
            "title": title,
            "meta_description": meta_desc,
            "viewport": meta_viewport,
            "h1_count": h1_count,
            "h2_count": len(parser.headings['h2']),
            "images_count": total_imgs,
            "images_missing_alt": missing_alt,
            "internal_links_count": len(parser.links),
            "cms_detected": cms_detected,
            "security_headers": sec_headers
        },
        "points_forts": points_forts,
        "alertes": alertes,
        "recommandations": recommandations
    }

def generate_markdown_report(audit_data):
    if not audit_data["success"]:
        return f"# Erreur lors de l'audit\n\nImpossible de contacter le site : {audit_data.get('error', 'Inconnu')}"

    score = audit_data["score"]
    color = "🟢" if score >= 80 else ("🟡" if score >= 50 else "🔴")
    
    report = []
    report.append(f"# 📊 Rapport d'Audit de Santé & SEO — {audit_data['url']}")
    report.append(f"**Date de l'analyse :** `{audit_data['date']}` | **Statut HTTP :** `{audit_data['status_code']}` | **Vitesse serveur :** `{audit_data['response_time_ms']} ms`\n")
    report.append(f"## {color} Score Global de Santé : **{score} / 100**\n")
    
    report.append("### 📈 Métriques Clés")
    report.append("| Indicateur | Valeur mesurée | Statut |")
    report.append("| :--- | :--- | :--- |")
    report.append(f"| **Vitesse de réponse** | `{audit_data['response_time_ms']} ms` | {'✅ Rapide' if audit_data['response_time_ms'] < 1000 else '⚠️ À optimiser'} |")
    report.append(f"| **Titre de la page** | `{audit_data['metrics']['title'] or 'Absent'}` | {'✅ Présent' if audit_data['metrics']['title'] else '❌ Manquant'} |")
    report.append(f"| **Meta Description** | `{len(audit_data['metrics']['meta_description'])} caractères` | {'✅ Optimal' if 50 <= len(audit_data['metrics']['meta_description']) <= 165 else '⚠️ À revoir'} |")
    report.append(f"| **Hiérarchie Titres H1** | `{audit_data['metrics']['h1_count']} balise(s) H1` | {'✅ Correct' if audit_data['metrics']['h1_count'] == 1 else '⚠️ Anormal'} |")
    report.append(f"| **Images sans attribut ALT** | `{audit_data['metrics']['images_missing_alt']} / {audit_data['metrics']['images_count']}` | {'✅ Aucune' if audit_data['metrics']['images_missing_alt'] == 0 else '⚠️ Manquantes'} |")
    report.append(f"| **Technologie / CMS** | `{audit_data['metrics'].get('cms_detected', 'Non détecté')}` | ℹ️ Détection IA |")
    report.append(f"| **Sécurité HSTS** | `{'Activé' if audit_data['metrics'].get('security_headers', {}).get('hsts') else 'Désactivé'}` | {'✅ Sécurisé' if audit_data['metrics'].get('security_headers', {}).get('hsts') else '⚠️ Recommandé'} |")
    report.append(f"| **Liens détectés** | `{audit_data['metrics']['internal_links_count']} liens` | ℹ️ Structure interne |\n")

    report.append("### ✅ Points Forts Détectés")
    for pt in audit_data["points_forts"]:
        report.append(f"- {pt}")
    report.append("")

    report.append("### ⚠️ Alertes & Points d'Amélioration")
    if audit_data["alertes"]:
        for al in audit_data["alertes"]:
            report.append(f"- {al}")
    else:
        report.append("- Aucune alerte majeure détectée !")
    report.append("")

    report.append("### 🎯 Plan d'Action Recommandé (Priorités)")
    if audit_data["recommandations"]:
        for i, rec in enumerate(audit_data["recommandations"], 1):
            report.append(f"{i}. {rec}")
    else:
        report.append("- Le site est parfaitement optimisé selon nos critères.")
    report.append("")
    
    report.append("---\n*Rapport automatisé généré par votre moteur SaaS.*")
    return "\n".join(report)

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    result = run_audit(url)
    
    os.makedirs("reports", exist_ok=True)
    slug = urllib.parse.urlparse(result["url"]).netloc.replace(".", "_") or "site"
    report_file = os.path.join("reports", f"audit_{slug}.md")
    
    md_content = generate_markdown_report(result)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print(f"[+] Rapport généré avec succès dans : {report_file}")
    print(f"[+] Score obtenu : {result.get('score', 0)}/100")
