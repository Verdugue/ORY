# Destiny 2 Hub

Une interface moderne pour afficher les informations de votre compte Destiny 2.

## Prérequis

- Python 3.8 ou supérieur
- Une clé API Bungie (obtenue sur https://www.bungie.net/en/Application)

## Installation

1. Clonez ce repository
2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

## Configuration

1. Allez sur https://www.bungie.net/en/Application
2. Créez une nouvelle application
3. Copiez votre clé API
4. Lancez l'application et collez votre clé API dans le champ prévu à cet effet sur la page d'accueil

## Utilisation

1. Lancez l'application :
```bash
python destiny_hub.py
```

2. Sur la page d'accueil :
   - Entrez votre clé API Bungie
   - Cliquez sur "Save API Key"

3. Sur la page Profile :
   - Entrez votre Bungie Name au format "Nom#1234"
   - Cliquez sur "Search Profile"
   - Vos informations de profil s'afficheront dans la zone de texte

## Fonctionnalités

- Interface moderne avec CustomTkinter
- Sauvegarde sécurisée de la clé API dans un fichier .env
- Affichage des informations de profil :
  - Date de dernière connexion
  - Temps de jeu total
  - Liste des personnages avec leurs caractéristiques
  - Niveau de lumière par personnage

## À venir

- Affichage des statistiques détaillées
- Suivi des objectifs
- Inventaire en temps réel
- Notifications d'événements 