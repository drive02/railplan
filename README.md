# 🚂 RailPlan — Tableau de Bord Ferroviaire

Application web de planification ferroviaire avec dashboard temps réel, export CSV et alertes email.

---

## 🖥️ Aperçu

- **3 lignes de rail** configurables avec timeline visuelle
- **Gestion des convois** : création, suivi, statuts en temps réel
- **Marchandises** : Orge, Blé, Maïs, Colza, Tournesol avec tonnage
- **Export CSV** filtrable (compatible Excel, avec BOM UTF-8)
- **Alertes email** SMTP configurables
- **Mode TV** plein écran pour affichage sur grand écran
- **Ticker** défilant avec les convois en cours

---

## 🚀 Démarrage rapide avec Docker

### Prérequis
- [Docker](https://www.docker.com/get-started) installé
- [Docker Compose](https://docs.docker.com/compose/install/) installé

### 1. Cloner le dépôt
```bash
git clone https://github.com/VOTRE_USERNAME/railplan.git
cd railplan
```

### 2. Configurer l'environnement
```bash
cp .env.example .env
# Éditez .env avec vos paramètres email si besoin
```

### 3. Lancer l'application
```bash
docker-compose up -d
```

### 4. Ouvrir dans le navigateur
```
http://localhost:5000
```

### Arrêter l'application
```bash
docker-compose down
```

---

## 🔄 Mise à jour depuis GitHub

Pour mettre à jour votre instance depuis le dépôt :

```bash
# Récupérer les dernières modifications
git pull origin main

# Reconstruire et relancer le conteneur
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 📧 Configuration des alertes email

Éditez votre fichier `.env` :

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=votre@gmail.com
MAIL_PASSWORD=votre_mot_de_passe_application
```

> **Gmail** : Créez un "mot de passe d'application" dans les paramètres de sécurité Google.

Puis redémarrez :
```bash
docker-compose restart
```

---

## 📥 Export CSV

L'export CSV est disponible :
- Via le bouton **⬇ EXPORT CSV** dans l'en-tête
- Via le bouton dans l'onglet **CONVOIS** (export filtré)
- Via l'API : `GET /api/export/csv?rail=1&cargo=Orge&status=En route`

Le fichier est encodé en **UTF-8 BOM** pour une ouverture directe dans Excel.

---

## 🔌 API REST

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/trains` | Liste des convois (filtrable) |
| POST | `/api/trains` | Créer un convoi |
| PUT | `/api/trains/<id>` | Modifier un convoi |
| DELETE | `/api/trains/<id>` | Supprimer un convoi |
| GET | `/api/export/csv` | Export CSV |
| GET | `/api/stats` | Statistiques globales |
| GET | `/api/alerts/config` | Config alertes |
| POST | `/api/alerts/config` | Sauvegarder config alertes |
| POST | `/api/alerts/test` | Envoyer email de test |

### Exemple : créer un convoi
```bash
curl -X POST http://localhost:5000/api/trains \
  -H "Content-Type: application/json" \
  -d '{
    "rail": 1,
    "cargo": "Blé",
    "tonnage": 2000,
    "client": "Mon Client",
    "depart": "2025-03-01T08:00",
    "arrivee": "2025-03-01T16:00"
  }'
```

---

## 🏗️ Structure du projet

```
railplan/
├── app.py                  # Backend Flask (API + BDD)
├── requirements.txt        # Dépendances Python
├── Dockerfile              # Image Docker
├── docker-compose.yml      # Orchestration
├── .env.example            # Variables d'environnement (modèle)
├── .gitignore
├── templates/
│   └── index.html          # Frontend (HTML/CSS/JS)
└── .github/
    └── workflows/
        └── ci.yml          # CI/CD GitHub Actions
```

---

## ⚙️ Variables d'environnement

| Variable | Défaut | Description |
|----------|--------|-------------|
| `DATABASE_URL` | `sqlite:////app/data/railplan.db` | URL base de données |
| `MAIL_SERVER` | `smtp.gmail.com` | Serveur SMTP |
| `MAIL_PORT` | `587` | Port SMTP |
| `MAIL_USERNAME` | — | Email expéditeur |
| `MAIL_PASSWORD` | — | Mot de passe SMTP |
| `DEBUG` | `false` | Mode debug Flask |

---

## 🛠️ Développement local (sans Docker)

```bash
python -m venv venv
source venv/bin/activate      # Windows : venv\Scripts\activate
pip install -r requirements.txt
DEBUG=true python app.py
```

---

## 📋 Lignes de rail

| ID | Nom | Couleur |
|----|-----|---------|
| 1 | Ligne A — Nord | 🟠 Orange |
| 2 | Ligne B — Est | 🟢 Vert |
| 3 | Ligne C — Ouest | 🟣 Violet |

---

## 📄 Licence

MIT — Libre d'utilisation et de modification.
