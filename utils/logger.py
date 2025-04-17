import logging
import sys
import os
from datetime import datetime
import psutil
import platform

def setup_logging():
    """Configure un système de logging détaillé."""
    try:
        # Créer un dossier logs s'il n'existe pas
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Créer un nouveau fichier de log avec timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f'logs/destiny_hub_{timestamp}.log'
        
        # Configuration du logging avec encodage UTF-8
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            handlers=[
                # Handler pour le fichier avec encodage UTF-8
                logging.FileHandler(log_filename, encoding='utf-8'),
                # Handler pour la console avec encodage UTF-8
                logging.StreamHandler(sys.stdout)
            ]
        )

        logging.info("=== Démarrage de Destiny Hub ===")
        logging.info(f"Version Python: {sys.version}")
        logging.info(f"Système d'exploitation: {sys.platform}")
        logging.info(f"Fichier de log créé: {log_filename}")
        
        # Log des informations système
        log_system_info()
        
    except Exception as e:
        print(f"Erreur lors de la configuration du logging: {str(e)}")
        sys.exit(1)

    # Vérifications de l'environnement
    try:
        check_environment()
        check_dependencies()
        check_files()
    except Exception as e:
        logging.error(f"Erreur lors des vérifications: {str(e)}")

def log_system_info():
    """Log les informations détaillées du système."""
    try:
        # Informations sur le système
        logging.info("=== Informations Système ===")
        logging.info(f"OS: {platform.system()} {platform.release()}")
        logging.info(f"Architecture: {platform.machine()}")
        logging.info(f"Processeur: {platform.processor()}")
        
        # Informations sur la mémoire
        mem = psutil.virtual_memory()
        logging.info(f"Mémoire totale: {mem.total / (1024**3):.2f} GB")
        logging.info(f"Mémoire disponible: {mem.available / (1024**3):.2f} GB")
        logging.info(f"Utilisation mémoire: {mem.percent}%")
        
        # Informations sur le disque
        disk = psutil.disk_usage('/')
        logging.info(f"Espace disque total: {disk.total / (1024**3):.2f} GB")
        logging.info(f"Espace disque libre: {disk.free / (1024**3):.2f} GB")
        logging.info(f"Utilisation disque: {disk.percent}%")
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des informations système: {str(e)}")

def check_environment():
    """Vérifie l'environnement d'exécution et les variables d'environnement."""
    logging.info("=== Vérification de l'environnement ===")
    
    try:
        # Vérifier les variables d'environnement
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = [
            'BUNGIE_API_KEY',
            'CLIENT_ID',
            'CLIENT_SECRET'
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            if value:
                logging.info(f"✓ {var} trouvée")
                logging.debug(f"Longueur de {var}: {len(value)}")
            else:
                logging.error(f"✗ {var} non trouvée dans .env")
                
    except ImportError:
        logging.error("Module python-dotenv non trouvé")
    except Exception as e:
        logging.error(f"Erreur lors de la vérification de l'environnement: {str(e)}")

def check_dependencies():
    """Vérifie les dépendances Python requises."""
    logging.info("=== Vérification des dépendances ===")
    
    dependencies = [
        ('PyQt6', 'PyQt6'),
        ('requests', 'requests'),
        ('python-dotenv', 'dotenv'),
        ('psutil', 'psutil'),
        ('beautifulsoup4', 'bs4')
    ]
    
    for package_name, module_name in dependencies:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'Version inconnue')
            logging.info(f"✓ {package_name} version: {version}")
        except ImportError as e:
            logging.error(f"✗ {package_name} non trouvé: {str(e)}")
            logging.info(f"Installation requise: pip install {package_name}")

def check_files():
    """Vérifie la présence des fichiers et dossiers nécessaires."""
    logging.info("=== Vérification des fichiers ===")
    
    required_files = [
        ('.env', 'Configuration'),
        ('main.py', 'Point d\'entrée'),
        ('requirements.txt', 'Dépendances')
    ]
    
    required_dirs = [
        ('ui', 'Interface utilisateur'),
        ('ui/pages', 'Pages de l\'interface'),
        ('api', 'API Bungie'),
        ('utils', 'Utilitaires'),
        ('data', 'Données'),
        ('icons', 'Icônes'),
        ('logs', 'Fichiers de log'),
        ('cache', 'Cache des images')
    ]
    
    # Vérifier les fichiers
    for file, description in required_files:
        if os.path.isfile(file):
            logging.info(f"✓ {file} trouvé ({description})")
            if file == 'requirements.txt':
                log_requirements_content(file)
        else:
            logging.error(f"✗ {file} manquant ({description})")
    
    # Vérifier les dossiers
    for directory, description in required_dirs:
        if os.path.isdir(directory):
            files = os.listdir(directory)
            logging.info(f"✓ Dossier {directory} trouvé ({description}) - {len(files)} fichiers")
            logging.debug(f"Contenu de {directory}: {', '.join(files)}")
        else:
            logging.warning(f"✗ Dossier {directory} manquant ({description})")
            try:
                os.makedirs(directory)
                logging.info(f"Dossier {directory} créé")
            except Exception as e:
                logging.error(f"Impossible de créer le dossier {directory}: {str(e)}")

def log_requirements_content(requirements_file):
    """Log le contenu du fichier requirements.txt."""
    try:
        with open(requirements_file, 'r') as f:
            requirements = f.readlines()
        logging.debug("=== Contenu de requirements.txt ===")
        for req in requirements:
            req = req.strip()
            if req and not req.startswith('#'):
                logging.debug(f"- {req}")
    except Exception as e:
        logging.error(f"Erreur lors de la lecture de requirements.txt: {str(e)}")

def log_error(error, context=""):
    """Fonction utilitaire pour logger les erreurs avec contexte."""
    error_message = f"{context}: {str(error)}" if context else str(error)
    logging.error(error_message)
    logging.debug("Détails de l'erreur:", exc_info=True)
    return error_message

def cleanup_old_logs(max_age_days=7):
    """Nettoie les anciens fichiers de log."""
    try:
        logs_dir = 'logs'
        if not os.path.exists(logs_dir):
            return
            
        current_time = datetime.now()
        for filename in os.listdir(logs_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(logs_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                age_days = (current_time - file_time).days
                
                if age_days > max_age_days:
                    os.remove(filepath)
                    logging.info(f"Ancien fichier de log supprimé: {filename}")
                    
    except Exception as e:
        logging.error(f"Erreur lors du nettoyage des logs: {str(e)}")