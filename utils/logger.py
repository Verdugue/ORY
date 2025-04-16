import logging
import sys
import os
from datetime import datetime

def setup_logging():
    """Configure un système de logging détaillé."""
    # Créer un nouveau fichier de log avec timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'destiny_hub_{timestamp}.log'
    
    # Configuration du logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[
            # Handler pour le fichier
            logging.FileHandler(log_filename),
            # Handler pour la console
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Log initial avec informations système
    logging.info("=== Démarrage de Destiny Hub ===")
    logging.info(f"Version Python: {sys.version}")
    logging.info(f"Système d'exploitation: {sys.platform}")
    
    # Vérification de l'environnement
    check_environment()
    check_dependencies()
    check_files()

def check_environment():
    """Vérifie l'environnement d'exécution."""
    logging.info("=== Vérification de l'environnement ===")
    
    # Vérifier les variables d'environnement
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('BUNGIE_API_KEY')
    if api_key:
        logging.info("✅ BUNGIE_API_KEY trouvée")
        logging.debug(f"Longueur de la clé API: {len(api_key)}")
    else:
        logging.error("❌ BUNGIE_API_KEY non trouvée dans .env")

def check_dependencies():
    """Vérifie les dépendances Python."""
    logging.info("=== Vérification des dépendances ===")
    
    dependencies = [
        ('PyQt6', 'PyQt6'),
        ('requests', 'requests'),
        ('python-dotenv', 'dotenv'),
        ('psutil', 'psutil')
    ]
    
    for package_name, module_name in dependencies:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'Version inconnue')
            logging.info(f"✅ {package_name} version: {version}")
        except ImportError as e:
            logging.error(f"❌ {package_name} non trouvé: {str(e)}")

def check_files():
    """Vérifie la présence des fichiers nécessaires."""
    logging.info("=== Vérification des fichiers ===")
    
    required_files = [
        ('.env', 'Configuration'),
        ('main.py', 'Point d\'entrée'),
    ]
    
    required_dirs = [
        ('ui', 'Interface utilisateur'),
        ('ui/pages', 'Pages de l\'interface'),
        ('api', 'API Bungie'),
        ('utils', 'Utilitaires'),
        ('data', 'Données'),
        ('icons', 'Icônes')
    ]
    
    # Vérifier les fichiers
    for file, description in required_files:
        if os.path.isfile(file):
            logging.info(f"✅ {file} trouvé ({description})")
        else:
            logging.error(f"❌ {file} manquant ({description})")
    
    # Vérifier les dossiers
    for directory, description in required_dirs:
        if os.path.isdir(directory):
            files = os.listdir(directory)
            logging.info(f"✅ Dossier {directory} trouvé ({description}) - {len(files)} fichiers")
            logging.debug(f"Contenu de {directory}: {', '.join(files)}")
        else:
            logging.error(f"❌ Dossier {directory} manquant ({description})")