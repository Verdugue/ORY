import sys
import os
from PyQt6.QtWidgets import QApplication
from ui.main_window import DestinyHub
from utils.logger import setup_logging
from utils.config import create_directories

def main():
    # Configurer le logging
    setup_logging()
    
    # Créer les répertoires nécessaires
    create_directories()
    
    # Lancer l'application
    app = QApplication(sys.argv)
    window = DestinyHub()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()