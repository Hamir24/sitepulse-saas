# 🚀 SitePulse AI

**Surveillance et audit quotidien de sites web, en SaaS.**
SitePulse analyse un site (vitesse, SEO, SSL, sécurité), lui donne une **note sur 100**, et envoie un rapport clair au client.

> 100% Python standard : **aucune dépendance à installer.**

<!-- 📸 Ajoute ici une capture d'écran : ![SitePulse](capture.png) -->

---

## ✨ Fonctionnalités

- **Audit d'un site en un clic** avec une note sur 100 et des recommandations.
- **Ce qui est vérifié :**
  - temps de réponse
  - HTTPS / certificat SSL
  - balise `<title>` et meta description
  - compatibilité mobile (viewport)
  - structure des titres H1
  - images sans balise `alt`
  - Open Graph (réseaux sociaux)
  - en-têtes de sécurité HTTP
  - détection du CMS / framework
- **Espace client** : inscription, connexion, ajout de ses propres sites (base SQLite).
- **Audit nocturne automatique** de tous les clients (`batch_audit.py`) + un *Master Digest* pour le fondateur.
- **Rapports** en Markdown et JSON, et **export PDF** (impression du navigateur).
- **Emails HTML** automatiques : Resend, SMTP, ou boîte d'envoi locale pour tester.
- **Abonnements** via des liens de paiement Stripe.
- **PWA** : installable sur téléphone.

---

## 🧱 Structure du projet

| Fichier | Rôle |
|---|---|
| `server.py` | Serveur web + API |
| `audit_engine.py` | Moteur d'audit (calcul de la note) |
| `batch_audit.py` | Audit de tous les clients de `clients.json` |
| `db.py` | Base SQLite : utilisateurs, sessions, sites, audits |
| `mailer.py` | Envoi des emails (Resend / SMTP / outbox) |
| `index.html` | Interface (site + espace client) |
| `clients.json` | Liste des clients à surveiller |
| `GUIDE_FONDATEUR.md` | Guide pour lancer et vendre le SaaS |

---

## ▶️ Lancer en local

Il faut **Python 3.8+**. C'est tout.

```bash
git clone https://github.com/Hamir24/sitepulse-saas.git
cd sitepulse-saas
python server.py
```

Puis ouvre **http://localhost:8080** (change le port avec la variable `PORT`).

Au premier lancement, un compte admin est créé : `admin@sitepulse.ai`.
Son mot de passe vient de la variable d'environnement `ADMIN_PASSWORD`.
Si tu ne la définis pas, un mot de passe aléatoire s'affiche **une seule fois** dans la console : note-le.

```bash
# Windows (PowerShell)
$env:ADMIN_PASSWORD="ton_mot_de_passe_solide"; python server.py

# Mac / Linux / Git Bash
ADMIN_PASSWORD="ton_mot_de_passe_solide" python server.py
```

### Lancer l'audit de tous les clients

```bash
python batch_audit.py
```

Les rapports arrivent dans `reports/<client>/` et le résumé dans `reports/master_digest_<date>.md`.

---

## ⚙️ Configuration

### Clients (`clients.json`)

```json
{
  "id": "client_03",
  "name": "Boulangerie Dupont",
  "url": "https://boulangerie-dupont.ci",
  "email": "contact@boulangerie-dupont.ci",
  "plan": "Pro (29€/mois)",
  "active": true
}
```

### Emails (variables d'environnement)

| Variable | Utilité |
|---|---|
| `ADMIN_PASSWORD` | Mot de passe du compte admin |
| `PORT` | Port du serveur (8080 par défaut) |
| `RESEND_API_KEY` | Envoi via Resend |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` | Envoi via SMTP |

Sans configuration, les emails sont enregistrés dans `reports/emails_outbox/` (pratique pour tester).

### Paiements Stripe (`config.json`)

Dans `config.json`, remplace les liens de test par tes vrais liens de paiement Stripe :

```json
{
  "stripe_settings": {
    "starter_payment_url": "https://buy.stripe.com/...",
    "pro_payment_url": "https://buy.stripe.com/...",
    "agency_payment_url": "https://buy.stripe.com/..."
  }
}
```

Le nom de chaque clé suit le modèle `<formule>_payment_url`. Tant qu'un lien contient `test_`, le site reste en mode démo.

> 🔒 Ne mets **jamais** de clé secrète (`sk_live_...`, mot de passe SMTP, clé Resend) dans ce fichier : utilise les variables d'environnement ci-dessus.

---

## 🔒 Sécurité

- Mots de passe hachés avec **PBKDF2-SHA256** (200 000 itérations).
- Seuls `index.html`, `manifest.json` et `success.html` sont servis publiquement.
- L'API des sites est réservée aux utilisateurs connectés.
- Limite de tentatives par adresse IP (connexion, inscription, audit, envoi d'email).

---

## ☁️ Déploiement

Le projet est prêt pour **Render** (`render.yaml` et `Procfile` inclus) :
commande de démarrage `python server.py`.

Sur Render, ajoute la variable d'environnement `ADMIN_PASSWORD` dans l'onglet *Environment*.
Le disque du plan gratuit est temporaire : la base SQLite est recréée à chaque déploiement.

---

## 🛣️ Pistes d'évolution

- Alertes quand un site tombe ou que sa note chute.
- Graphique d'évolution de la note dans le temps.
- Paiement mobile (Orange Money, MTN MoMo, Wave) pour les clients en Côte d'Ivoire.

---

## 👤 Auteur

**Ibrahima Diallo**
Étudiant BTS Réseau Informatique et Télécommunication (RIT), Côte d'Ivoire
GitHub : [@Hamir24](https://github.com/Hamir24)
