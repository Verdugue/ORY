from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QStackedWidget, QToolBar, QStatusBar, QToolButton,
                           QLabel, QPushButton)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont
from ui.pages.account_page import AccountPage
from ui.pages.equipment_page import EquipmentPage
from ui.pages.missions_page import MissionsPage
from ui.styles import setup_dark_theme, GLOBAL_STYLE
import logging
import os

class DestinyHub(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.info("=== Initialisation de la fenêtre principale ===")
        
        self.setWindowTitle("Destiny 2 Hub")
        self.setMinimumSize(1000, 600)
        
        try:
            self.setup_ui()
            self.setup_statusbar()
            self.setup_styles()
            logging.info("✅ Interface principale initialisée avec succès")
        except Exception as e:
            logging.error(f"❌ Erreur lors de l'initialisation de l'interface: {str(e)}")
            logging.exception("Détails de l'erreur:")

    def setup_ui(self):
        logging.info("Configuration de l'interface utilisateur")
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal vertical
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # En-tête avec titre et navigation
        header = QWidget()
        header.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-bottom: 1px solid #333;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        # Titre
        title_label = QLabel("Destiny 2 Hub")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(title_label)
        
        # Boutons de navigation
        nav_buttons = QHBoxLayout()
        nav_buttons.setSpacing(5)
        
        self.nav_buttons = []
        for text, icon_path in [
            ("Compte", "icons/account.png"),
            ("Équipement", "icons/equipment.png"),
            ("Missions", "icons/missions.png")
        ]:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    color: white;
                    background-color: transparent;
                    border: none;
                    padding: 8px 15px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #333;
                }
                QPushButton:checked {
                    background-color: #444;
                    border-bottom: 2px solid #4d7aff;
                }
            """)
            
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
            
            nav_buttons.addWidget(btn)
            self.nav_buttons.append(btn)
        
        header_layout.addLayout(nav_buttons)
        header_layout.addStretch()
        
        # Ajouter l'en-tête au layout principal
        main_layout.addWidget(header)
        
        try:
            # Stacked widget pour les pages
            self.stacked_widget = QStackedWidget()
            
            # Créer les pages
            logging.debug("Création des pages...")
            self.account_page = AccountPage(self)
            logging.debug("✓ Page compte créée")
            
            self.equipment_page = EquipmentPage(self)
            logging.debug("✓ Page équipement créée")
            
            self.missions_page = MissionsPage(self)
            logging.debug("✓ Page missions créée")
            
            # Ajouter les pages
            self.stacked_widget.addWidget(self.account_page)
            self.stacked_widget.addWidget(self.equipment_page)
            self.stacked_widget.addWidget(self.missions_page)
            
            # Connecter les boutons aux pages
            self.nav_buttons[0].clicked.connect(lambda: self.switch_page(0))
            self.nav_buttons[1].clicked.connect(lambda: self.switch_page(1))
            self.nav_buttons[2].clicked.connect(lambda: self.switch_page(2))
            
            # Sélectionner la première page par défaut
            self.nav_buttons[0].setChecked(True)
            
            main_layout.addWidget(self.stacked_widget)
            logging.info("✅ Pages ajoutées avec succès")
            
        except Exception as e:
            logging.error(f"❌ Erreur lors de la création des pages: {str(e)}")
            logging.exception("Détails de l'erreur:")

    def setup_statusbar(self):
        logging.info("Configuration de la barre de statut")
        
        try:
            status_bar = QStatusBar()
            status_bar.setStyleSheet("""
                QStatusBar {
                    background-color: #1a1a1a;
                    color: #888;
                    border-top: 1px solid #333;
                }
            """)
            self.setStatusBar(status_bar)
            status_bar.showMessage("Prêt")
            logging.info("✅ Barre de statut configurée")
            
        except Exception as e:
            logging.error(f"❌ Erreur lors de la configuration de la barre de statut: {str(e)}")

    def setup_styles(self):
        logging.info("Application des styles")
        
        try:
            setup_dark_theme(self)
            self.setStyleSheet(GLOBAL_STYLE)
            logging.info("✅ Styles appliqués")
            
        except Exception as e:
            logging.error(f"❌ Erreur lors de l'application des styles: {str(e)}")

    def switch_page(self, index):
        logging.info(f"Changement de page vers l'index {index}")
        try:
            # Changer la page
            self.stacked_widget.setCurrentIndex(index)
            
            # Mettre à jour l'état des boutons
            for i, btn in enumerate(self.nav_buttons):
                btn.setChecked(i == index)
            
            logging.debug(f"✓ Page changée avec succès vers {index}")
        except Exception as e:
            logging.error(f"❌ Erreur lors du changement de page: {str(e)}")
            logging.exception("Détails de l'erreur:")

    def update_status(self, message):
        """Met à jour le message de la barre de statut."""
        try:
            self.statusBar().showMessage(message)
            logging.debug(f"Status mis à jour: {message}")
        except Exception as e:
            logging.error(f"❌ Erreur lors de la mise à jour du status: {str(e)}")