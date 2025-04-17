from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, 
                           QLineEdit, QPushButton, QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt
import logging
import json
import requests
import os
from api.bungie_client import BungieClient
from utils.config import OAUTH_CONFIG

class AccountPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialiser le logger
        self.logger = logging.getLogger(__name__)
        self.bungie_client = BungieClient()
        self.setup_ui()
        self.load_saved_account()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Groupe Compte
        account_group = QGroupBox("Compte Destiny 2")
        account_layout = QVBoxLayout()
        
        # Statut du compte avec style
        self.account_status = QLabel("Aucun compte enregistré")
        self.account_status.setStyleSheet("""
            QLabel {
                padding: 10px;
                border-radius: 5px;
                background-color: rgba(255, 0, 0, 0.1);
                color: #ff4444;
            }
        """)
        account_layout.addWidget(self.account_status)
        
        # Input Bungie Name avec style
        self.bungie_name_input = QLineEdit()
        self.bungie_name_input.setPlaceholderText("Entrez votre Bungie Name (ex: per#8639)")
        self.bungie_name_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                font-size: 14px;
                border: 1px solid #3d3f43;
                border-radius: 4px;
                background-color: #2a2c30;
                color: white;
            }
            QLineEdit:focus {
                border: 1px solid #4d7aff;
            }
        """)
        account_layout.addWidget(self.bungie_name_input)
        
        # Bouton d'enregistrement avec style
        self.save_button = QPushButton("Enregistrer le compte")
        self.save_button.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                background-color: #4d7aff;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5d8aff;
            }
            QPushButton:pressed {
                background-color: #3d6aff;
            }
        """)
        self.save_button.clicked.connect(self.register_account)
        account_layout.addWidget(self.save_button)
        
        account_group.setLayout(account_layout)
        layout.addWidget(account_group)
        
        # Informations du compte
        self.account_info = QTextEdit()
        self.account_info.setReadOnly(True)
        self.account_info.setStyleSheet("""
            QTextEdit {
                background-color: #2a2c30;
                border: 1px solid #3d3f43;
                border-radius: 4px;
                color: white;
                padding: 10px;
            }
        """)
        layout.addWidget(self.account_info)

    def register_account(self):
        """Enregistre un nouveau compte Destiny 2."""
        try:
            bungie_name = self.bungie_name_input.text().strip()
            self.logger.info(f"Tentative d'enregistrement du compte: {bungie_name}")
            
            if not bungie_name or '#' not in bungie_name:
                self.show_error("Format de Bungie Name invalide (ex: Guardian#1234)")
                return

            display_name, display_name_code = bungie_name.split('#')
            
            # Vérifier la clé API
            if not OAUTH_CONFIG['api_key']:
                self.show_error("Clé API Bungie non configurée")
                return
            
            # Faire la requête
            response = requests.post(
                'https://www.bungie.net/Platform/Destiny2/SearchDestinyPlayerByBungieName/-1/',
                headers={'X-API-Key': OAUTH_CONFIG['api_key']},
                json={
                    'displayName': display_name,
                    'displayNameCode': int(display_name_code)
                }
            )
            
            self.logger.info(f"Réponse reçue - Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('Response'):
                    # Sauvegarder les données
                    if not os.path.exists('data'):
                        os.makedirs('data')
                    
                    with open('data/account.json', 'w') as f:
                        json.dump(response_data, f, indent=4)
                    self.logger.info("Données du compte sauvegardées")
                    
                    # Mettre à jour l'interface
                    self.account_status.setText(f"Compte enregistré: {bungie_name}")
                    self.account_status.setStyleSheet("color: green;")
                    
                    # Actualiser l'équipement automatiquement
                    main_window = self.window()
                    if hasattr(main_window, 'equipment_page'):
                        self.logger.info("Actualisation automatique de l'équipement")
                        main_window.equipment_page.refresh_character_data()
                        # Changer automatiquement vers la page d'équipement
                        main_window.switch_page(1)
                    
                    self.show_success("Compte enregistré avec succès!")
                else:
                    self.show_error("Compte Destiny 2 non trouvé")
            else:
                error_msg = f"Erreur API: {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        error_msg += f"\n{error_data.get('Message', '')}"
                    except:
                        error_msg += f"\n{response.text}"
                self.show_error(error_msg)
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement du compte: {str(e)}")
            self.show_error(f"Erreur lors de l'enregistrement: {str(e)}")

    def save_account_data(self, data):
        """Sauvegarde les données du compte."""
        try:
            with open('data/account.json', 'w') as f:
                json.dump(data, f, indent=4)
            logging.info("Données du compte sauvegardées")
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde des données: {str(e)}")
            raise

    def load_saved_account(self):
        """Charge les informations du compte sauvegardé."""
        try:
            if os.path.exists('data/account.json'):
                with open('data/account.json', 'r') as f:
                    data = json.load(f)
                if data.get('Response'):
                    self.update_account_status("Compte connecté", True)
                    self.display_account_info(data['Response'][0])
                    return True
        except Exception as e:
            logging.error(f"Erreur lors du chargement du compte: {str(e)}")
        return False

    def display_account_info(self, profile):
        """Affiche les informations du compte."""
        try:
            info_text = "Informations du compte:\n\n"
            info_text += f"Bungie Name: {profile.get('displayName')}#{profile.get('displayNameCode')}\n"
            info_text += f"Membership ID: {profile.get('membershipId')}\n"
            info_text += f"Plateforme: {self.get_platform_name(profile.get('membershipType'))}\n"
            
            self.account_info.setText(info_text)
            
        except Exception as e:
            logging.error(f"Erreur lors de l'affichage des informations: {str(e)}")

    def get_platform_name(self, membership_type):
        """Retourne le nom de la plateforme basé sur le membershipType."""
        platforms = {
            1: "Xbox",
            2: "PlayStation",
            3: "Steam",
            4: "Battle.net",
            5: "Stadia",
            6: "Epic Games",
            10: "Demon",
            254: "BungieNext"
        }
        return platforms.get(membership_type, "Inconnu")

    def update_account_status(self, message, success=False):
        """Met à jour le statut du compte avec le style approprié."""
        self.account_status.setText(message)
        if success:
            self.account_status.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    border-radius: 5px;
                    background-color: rgba(46, 204, 113, 0.1);
                    color: #2ecc71;
                }
            """)
        else:
            self.account_status.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    border-radius: 5px;
                    background-color: rgba(255, 0, 0, 0.1);
                    color: #ff4444;
                }
            """)

    def show_error(self, message):
        """Affiche une boîte de dialogue d'erreur."""
        QMessageBox.warning(self, "Erreur", message)
        self.logger.error(message)

    def show_success(self, message):
        """Affiche une boîte de dialogue de succès."""
        QMessageBox.information(self, "Succès", message)
        self.logger.info(message)