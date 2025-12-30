# IRELEC – Système de Gestion de Facturation d'Électricité (MVP)

![IRELEC Banner](https://img.shields.io/badge/IRELEC-Électricité-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red)
![Status](https://img.shields.io/badge/Status-MVP-yellow)

## 📋 Aperçu du Projet

**IRELEC** est un système de gestion de facturation d'électricité inspiré de ENEO Cameroon. Cette application MVP (Minimum Viable Product) démontre les fonctionnalités essentielles d'un système de facturation électrique dans un environnement utilisateur simple et intuitif.

### ⚠️ **Note importante : Ceci est un MVP**
Cette application représente une **version démonstration** (Minimum Viable Product) avec les objectifs suivants :
- ✅ Valider les fonctionnalités principales
- ✅ Présenter le concept aux clients potentiels
- ✅ Obtenir des retours avant développement complet
- **❌ PAS une version de production**

---

## 🎯 Fonctionnalités Principales

### 1. **Gestion des Clients** 👥
- Ajout de nouveaux clients avec informations complètes
- Visualisation de la base de données clients
- Sélection facile des clients pour les opérations

**Champs client :**
- Nom complet
- Numéro de compteur (unique)
- Numéro de contrat (unique)
- Localisation
- Tarif personnalisé (FCFA/kWh)

### 2. **Consommation & Facturation** 💡
- Saisie des index de compteur
- Calcul automatique de la consommation
- Calcul du montant basé sur le tarif
- Validation des données (index croissants)

### 3. **Génération de Factures** 📄
- Facture au format professionnel (style ENEO)
- Informations client complètes
- Détails de consommation clairs
- Export en PDF (fonctionnalité bonus)

### 4. **Historique des Factures** 📜
- Archivage automatique des factures
- Filtrage par client et par mois
- Consultation des factures précédentes
- Statistiques de revenus

---

## 🛠️ Technologies Utilisées

| Technologie | Version | Rôle |
|------------|---------|------|
| **Python** | 3.8+ | Langage principal |
| **Streamlit** | 1.28+ | Interface utilisateur web |
| **Pandas** | 2.1+ | Manipulation des données |
| **SQLite** | 3.35+ | Base de données locale |
| **FPDF2** | 2.7+ | Génération de PDF |

---

## 🚀 Installation et Démarrage

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Installation étape par étape

1. **Cloner/Initialiser le projet**
```bash
# Créer un dossier pour le projet
mkdir irelec-mvp
cd irelec-mvp
```

2. **Installer les dépendances**
```bash
# Méthode recommandée (avec timeout augmenté)
pip install --default-timeout=100 streamlit pandas fpdf2

# OU avec miroir alternatif (si connexion lente)
pip install streamlit pandas fpdf2 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

3. **Créer le fichier principal**
```bash
# Copier le code app.py dans ce dossier
# Ou créer un nouveau fichier app.py
```

4. **Lancer l'application**
```bash
streamlit run app.py
```

5. **Accéder à l'application**
- Ouvrez votre navigateur
- Allez à : `http://localhost:8501`
- Ou suivez le lien affiché dans le terminal

---

## 🗂️ Structure du Projet

```
irelec-mvp/
│
├── app.py                    # Application principale Streamlit
├── requirements.txt          # Dépendances Python (optionnel)
├── irelec.db                # Base de données SQLite (auto-générée)
│
├── README.md                # Ce fichier
└── (Optionnel) fonts/       # Polices DejaVu pour PDF Unicode
```

---

## 📊 Base de Données

L'application utilise **SQLite** avec 2 tables principales :

### Table `clients`
```sql
CREATE TABLE clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_complet TEXT NOT NULL,
    numero_compteur TEXT UNIQUE NOT NULL,
    numero_contrat TEXT UNIQUE NOT NULL,
    localisation TEXT,
    tarif REAL NOT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Table `factures`
```sql
CREATE TABLE factures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    numero_facture TEXT UNIQUE,
    index_precedent REAL,
    index_actuel REAL,
    consommation REAL,
    tarif REAL,
    montant_total REAL,
    date_facture TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients (id)
)
```

---

## 🎨 Fonctionnement de l'Application

### Navigation
L'application comporte 4 sections principales accessibles via la barre latérale :

1. **📊 Tableau de Bord**  
   Vue d'ensemble avec statistiques et activité récente

2. **👥 Gestion Clients**  
   Ajout et gestion de la base clients

3. **💡 Consommation & Facturation**  
   Saisie des index et génération de factures

4. **📜 Historique Factures**  
   Consultation et filtrage des factures passées

### Workflow Type
```
1. Ajouter un client
2. Sélectionner le client
3. Saisir les index du compteur
4. Calculer et vérifier la facture
5. Générer la facture (sauvegarde automatique)
6. Consulter l'historique si besoin
```

---

## 🎯 Objectifs du MVP

### ✅ **Réalisés**
- [x] Gestion complète du cycle client-facture
- [x] Interface utilisateur intuitive
- [x] Persistance des données
- [x] Génération de PDF
- [x] Filtrage et recherche
- [x] Validation des données

### 🔄 **Pour Version Future**
- [ ] Système d'authentification
- [ ] Notifications par email
- [ ] Tableau de bord avancé
- [ ] API REST
- [ ] Multi-utilisateurs
- [ ] Rapports statistiques détaillés

---

## ⚠️ Limitations du MVP

1. **Pas d'authentification**  
   L'application est accessible à tous les utilisateurs du réseau

2. **Base de données locale**  
   Les données sont stockées localement (fichier SQLite)

3. **Monoposte**  
   Conçu pour un seul utilisateur à la fois

4. **Pas de sauvegarde cloud**  
   Les données restent sur la machine locale

5. **Interface basique**  
   Design minimaliste pour validation fonctionnelle

---

## 🔧 Dépannage

### Problèmes Courants

**1. Erreur d'installation pip**
```bash
# Solution : Augmenter le timeout
pip install --default-timeout=200 streamlit pandas fpdf2
```

**2. Problème de caractères dans le PDF**
```bash
# Installer les polices DejaVu
# Téléchargez depuis : https://dejavu-fonts.github.io/
# Placez les fichiers .ttf dans le dossier du projet
```

**3. Port déjà utilisé**
```bash
# Spécifier un port différent
streamlit run app.py --server.port 8502
```

**4. Base de données corrompue**
```bash
# Supprimer le fichier et redémarrer
rm irelec.db
streamlit run app.py
```

### Logs d'erreur
Consultez les messages dans le terminal pour identifier les problèmes spécifiques.

---

## 📈 Améliorations Possibles

### Priorité Haute
1. **Authentification** - Protection par mot de passe
2. **Sauvegarde automatique** - Export régulier des données
3. **Template PDF personnalisable** - Logo entreprise

### Priorité Moyenne
4. **Import/Export Excel** - Données clients/factures
5. **Calculs avancés** - Taxes, frais supplémentaires
6. **Notifications** - Rappels de paiement

### Priorité Basse
7. **Multi-langues** - Français/Anglais
8. **Thèmes personnalisables** - Couleurs entreprise
9. **API webhooks** - Intégration avec autres systèmes

---

## 🤝 Contribution

Bien que ce soit un MVP, les retours sont appréciés :

1. **Signaler un bug**  
   Décrivez le problème avec les étapes pour le reproduire

2. **Suggérer une amélioration**  
   Proposez de nouvelles fonctionnalités ou améliorations

3. **Partager des retours**  
   Expérience utilisateur, interface, etc.

---

## 📄 Licence

Ce projet est fourni **à titre de démonstration**.  
Il peut être utilisé librement pour :
- Apprentissage et éducation
- Prototypes et démonstrations
- Projets personnels

**Restrictions :**
- Usage commercial nécessite autorisation
- Ne pas redistribuer sans modifications substantielles
- Citer l'auteur original si utilisé publiquement

---

## 📞 Support

Pour toute question concernant ce MVP :
- Consultez les [Issues GitHub] (si disponible)
- Vérifiez les logs d'erreur dans le terminal
- Consultez la documentation Streamlit

**Rappel :** Ceci est un MVP destiné à la démonstration, pas un produit finalisé.

---

## 🎉 Démarrage Rapide

```bash
# En 3 commandes seulement !
git clone <repository>  # Si disponible
pip install streamlit pandas fpdf2
streamlit run app.py
```

Ouvrez votre navigateur et commencez à gérer vos factures d'électricité ! ⚡

---

**Développé avec ❤️ pour la gestion énergétique en Afrique**  
*"Simplifier la facturation électrique, une communauté à la fois"*
