# 🚀 Guide Fondateur — Lancer & Vendre Votre SaaS Sans Savoir Coder

Bienvenue dans votre projet **SitePulse AI**.

Toute l'infrastructure technique est désormais en place et fonctionne de manière autonome. Vous n'avez pas besoin d'écrire une seule ligne de code. Voici exactement comment l'utiliser et comment trouver vos premiers clients payants.

---

## 🏗️ 1. Comment fonctionne votre système

1. **L'automatisation nocturne (Antigravity Schedule)** :
   * Chaque nuit à minuit UTC (`0 0 * * *`), l'agent démarre automatiquement.
   * Il exécute `batch_audit.py`.
2. **La tournée des sites** :
   * Le script lit votre fichier `clients.json`.
   * Il analyse chaque site : vitesse de chargement, erreurs SEO, images sans balises, certificat de sécurité SSL.
3. **La production des livrables** :
   * Les rapports individuels pour chaque client sont sauvegardés dans `reports/<nom_du_client>/`.
   * Un **Master Digest** récapitulatif pour vous est généré dans `reports/master_digest_<date>.md`.

---

## 👥 2. Comment ajouter un nouveau client (30 secondes)

Pour mettre un nouveau client sous surveillance, ouvrez simplement le fichier `clients.json` et ajoutez son site dans la liste :

```json
{
  "id": "client_03",
  "name": "Boulangerie Dupont",
  "url": "https://boulangerie-dupont-paris.fr",
  "email": "contact@dupont.fr",
  "plan": "Pro (49€/mois)",
  "active": true
}
```

Dès la nuit suivante, son site sera automatiquement audité et son rapport sera généré !

---

## 🎯 3. La méthode infaillible pour décrocher vos 3 premiers clients (0€ de pub)

Comme vous avez un moteur d'audit déjà prêt, vous avez une arme de vente massive : **l'audit gratuit d'accroche**.

### Étape A : Repérez 5 sites de PME ou commerces locaux
Prenez des entreprises de votre ville ou de votre réseau qui ont un site web (artisans, boutiques en ligne, agences immobilières, restaurants, cabinets comptables).

### Étape B : Générez leur rapport en 1 clic
Lancez le moteur sur leur site :
```bash
python audit_engine.py https://adresse-de-leur-site.fr
```
Le rapport d'audit est créé instantanément dans le dossier `reports/`.

### Étape C : Envoyez-leur cet e-mail percutant
> **Objet :** 3 anomalies détectées sur votre site [Nom du site]
> 
> *Bonjour [Nom du gérant],*
> 
> *J'ai effectué une analyse de routine de la santé technique et du référencement naturel de votre site web cette nuit.*
> 
> *Votre score actuel est de [X]/100. J'ai notamment repéré [ex: un temps de chargement ralenti / plusieurs images sans description / des balises SEO manquantes] qui peuvent pénaliser votre visibilité sur Google.*
> 
> *Je vous joins le rapport complet en pièce jointe, c'est totalement offert.*
> 
> *Si vous souhaitez que notre robot surveille automatiquement votre site chaque nuit et vous alerte de la moindre panne ou anomalie pour 29€/mois, dites-le moi simplement par retour de mail.*
> 
> *Bien cordialement,*
> *[Votre Prénom]*

💡 **Pourquoi ça marche ?** Parce que vous n'essayez pas de leur vendre du vent : vous leur apportez une preuve concrète et chiffrée dès le premier message.

---

## 💳 4. Comment encaisser les abonnements

1. Créez un compte gratuit sur [Stripe.com](https://stripe.com).
2. Dans le menu **Produits**, créez un abonnement nommé : `Surveillance Web Pro - 29€ / mois` (ou 49€).
3. Cliquez sur **Créer un lien de paiement** (Stripe Payment Link).
4. Dès qu'un client dit oui, envoyez-lui ce lien sécurisé pour qu'il renseigne sa carte bancaire.
5. Vous touchez votre revenu récurrent chaque mois.

---

## 💻 5. Votre tableau de bord & vitrine

Vous disposez d'une page de présentation moderne déjà créée :
* Fichier : `index.html`
* Vous pouvez faire un double-clic dessus pour l'ouvrir dans Chrome, Edge ou Firefox et voir votre tableau de bord en direct !
