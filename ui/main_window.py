from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QStackedWidget, QToolBar, QStatusBar, QToolButton,
                           QLabel, QPushButton, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont
from ui.pages.account_page import AccountPage
from ui.pages.equipment_page import EquipmentPage
from ui.pages.missions_page import MissionsPage
from ui.pages.meta_page import MetaPage
from ui.styles import setup_dark_theme, GLOBAL_STYLE
import logging
import os

class DestinyHub(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.info("=== Initialisation de la fenêtre principale ===")
        
        self.setWindowTitle("Destiny 2 Hub")
        self.setMinimumSize(1000, 600)
        self.meta_page = None  # Ajouté : page meta non créée au départ
        
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
        header_layout.setSpacing(20)  # <-- Ajoute un peu d'espace entre titre et onglets
        
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
        self.language_selector = QComboBox()
        self.language_selector.addItem("Français", "fr")
        self.language_selector.addItem("English", "en")
        self.language_selector.addItem("Deutsch", "de")
        self.language_selector.addItem("Español", "es")
        self.language_selector.addItem("Italiano", "it")
        self.language_selector.addItem("日本語", "ja")
        self.language_selector.addItem("Português (Brasil)", "pt-br")
        self.language_selector.addItem("Русский", "ru")
        self.language_selector.addItem("Polski", "pl")
        self.language_selector.addItem("中文(简体)", "zh-chs")
        self.language_selector.addItem("中文(繁體)", "zh-cht")
        self.language_selector.addItem("한국어", "ko")
        self.language_selector.setCurrentIndex(0)
        self.language_selector.currentIndexChanged.connect(self.on_language_changed)
        header_layout.addWidget(self.language_selector)
        self.selected_locale = "fr"
        
        # Barre d'onglets (juste à droite du titre)
        self.nav_buttons = []
        nav_bar = QHBoxLayout()
        nav_bar.setSpacing(0)
        for idx, (text, icon_path) in enumerate([
            ("Compte", "icons/account.png"),
            ("Équipement", "icons/equipment.png"),
            ("Missions", "icons/missions.png"),
            ("Meta", "icons/meta.png")
        ]):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setStyleSheet("""
                QPushButton {
                    color: white;
                    background-color: transparent;
                    border: none;
                    padding: 8px 20px;
                    font-size: 15px;
                }
                QPushButton:hover {
                    background-color: #333;
                }
                QPushButton:checked {
                    background-color: #444;
                    border-bottom: 3px solid #4d7aff;
                }
            """)
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
            btn.clicked.connect(lambda checked, i=idx: self.switch_page(i))
            nav_bar.addWidget(btn)
            self.nav_buttons.append(btn)
        header_layout.addLayout(nav_bar)
        header_layout.addStretch()  # Le stretch pousse tout à gauche
        
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
            
            # Sélectionner la première page par défaut
            self.nav_buttons[0].setChecked(True)
            self.stacked_widget.setCurrentIndex(0)
            
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
            # Si on clique sur l'onglet Meta (dernier index)
            if index == 3:
                if self.meta_page is None:
                    self.meta_page = MetaPage(self)
                    self.stacked_widget.addWidget(self.meta_page)
                self.stacked_widget.setCurrentWidget(self.meta_page)
            else:
                self.stacked_widget.setCurrentIndex(index)
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

    def on_language_changed(self, index):
        self.selected_locale = self.language_selector.currentData()
        # Rafraîchir la page équipements si elle est affichée
        if self.stacked_widget.currentWidget() == self.equipment_page:
            self.equipment_page.set_locale(self.selected_locale)
            self.equipment_page.refresh_character_data()