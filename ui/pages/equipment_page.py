from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QComboBox, QPushButton, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
import logging
import os
import json
import requests
from utils.config import OAUTH_CONFIG, BUCKET_TYPES

class EquipmentPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        logging.info("=== Initialisation de la page Équipement ===")
        self.setup_ui()
        self.load_characters()  # Charger les personnages au démarrage

    def setup_ui(self):
        try:
            logging.info("Configuration de l'interface équipement")
            layout = QVBoxLayout(self)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(20)

            # Contrôles supérieurs
            top_controls = QHBoxLayout()
            
            # Sélecteur de personnage
            self.character_selector = QComboBox()
            self.character_selector.setStyleSheet("""
                QComboBox {
                    background-color: #2a2c30;
                    color: white;
                    padding: 8px;
                    border: 1px solid #3d3f43;
                    border-radius: 4px;
                    min-width: 200px;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: url(icons/arrow-down.png);
                    width: 12px;
                    height: 12px;
                }
                QComboBox QAbstractItemView {
                    background-color: #2a2c30;
                    color: white;
                    selection-background-color: #4d7aff;
                }
            """)
            self.character_selector.currentIndexChanged.connect(self.on_character_changed)
            top_controls.addWidget(self.character_selector)
            
            # Bouton d'actualisation
            self.refresh_button = QPushButton("Actualiser l'équipement")
            self.refresh_button.setStyleSheet("""
                QPushButton {
                    background-color: #4d7aff;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5d8aff;
                }
                QPushButton:pressed {
                    background-color: #3d6aff;
                }
            """)
            self.refresh_button.clicked.connect(self.refresh_character_data)
            top_controls.addWidget(self.refresh_button)
            top_controls.addStretch()

            layout.addLayout(top_controls)
            
            # Layout principal de l'équipement
            equipment_layout = QHBoxLayout()
            
            # Colonnes d'équipement
            self.weapons_column = self.create_weapons_column()
            self.character_widget = self.create_character_widget()
            self.armor_column = self.create_armor_column()
            
            equipment_layout.addLayout(self.weapons_column)
            equipment_layout.addWidget(self.character_widget)
            equipment_layout.addLayout(self.armor_column)
            
            layout.addLayout(equipment_layout)
            
            logging.info("✅ Interface équipement configurée avec succès")
            
        except Exception as e:
            logging.error(f"❌ Erreur lors de la configuration de l'interface équipement: {str(e)}")
            logging.exception("Détails de l'erreur:")

    def create_weapons_column(self):
        """Crée la colonne des armes."""
        try:
            logging.info("Création de la colonne des armes")
            weapons_layout = QVBoxLayout()
            weapons_layout.setSpacing(10)
            
            self.weapon_slots = []
            weapon_types = ['Cinétique', 'Énergie', 'Puissance']
            
            for weapon_type in weapon_types:
                # Créer le groupe pour l'arme
                slot = QGroupBox(weapon_type)
                slot.setStyleSheet("""
                    QGroupBox {
                        background-color: rgba(35, 37, 41, 0.7);
                        border: 1px solid #3d3f43;
                        border-radius: 4px;
                        padding: 10px;
                        margin-top: 5px;
                    }
                    QGroupBox::title {
                        color: #4d7aff;
                        font-weight: bold;
                        font-size: 14px;
                    }
                """)
                
                slot_layout = QVBoxLayout(slot)
                slot_layout.setSpacing(5)
                
                # Icône
                icon_label = QLabel()
                icon_label.setFixedSize(64, 64)
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                icon_label.setStyleSheet("background-color: rgba(0, 0, 0, 0.3); border-radius: 4px;")
                slot_layout.addWidget(icon_label)
                
                # Puissance
                power_label = QLabel("0")
                power_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                power_label.setStyleSheet("color: #FFEB3B; font-weight: bold; font-size: 16px;")
                slot_layout.addWidget(power_label)
                
                # Nom
                name_label = QLabel("Vide")
                name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                name_label.setWordWrap(True)
                name_label.setStyleSheet("color: white; font-size: 12px;")
                slot_layout.addWidget(name_label)
                
                weapons_layout.addWidget(slot)
                self.weapon_slots.append(slot)
            
            weapons_layout.addStretch()
            logging.info("✅ Colonne des armes créée avec succès")
            return weapons_layout
            
        except Exception as e:
            logging.error(f"❌ Erreur lors de la création de la colonne des armes: {str(e)}")
            logging.exception("Détails de l'erreur:")
            return QVBoxLayout()

    def create_armor_column(self):
        """Crée la colonne de l'armure."""
        try:
            logging.info("Création de la colonne de l'armure")
            armor_layout = QVBoxLayout()
            armor_layout.setSpacing(10)
            
            self.armor_slots = []
            armor_types = ['Casque', 'Gants', 'Torse', 'Jambes', 'Marque']
            
            for armor_type in armor_types:
                # Créer le groupe pour l'armure
                slot = QGroupBox(armor_type)
                slot.setStyleSheet("""
                    QGroupBox {
                        background-color: rgba(35, 37, 41, 0.7);
                        border: 1px solid #3d3f43;
                        border-radius: 4px;
                        padding: 10px;
                        margin-top: 5px;
                    }
                    QGroupBox::title {
                        color: #4d7aff;
                        font-weight: bold;
                        font-size: 14px;
                    }
                """)
                
                slot_layout = QVBoxLayout(slot)
                slot_layout.setSpacing(5)
                
                # Icône
                icon_label = QLabel()
                icon_label.setFixedSize(64, 64)
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                icon_label.setStyleSheet("background-color: rgba(0, 0, 0, 0.3); border-radius: 4px;")
                slot_layout.addWidget(icon_label)
                
                # Puissance
                power_label = QLabel("0")
                power_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                power_label.setStyleSheet("color: #FFEB3B; font-weight: bold; font-size: 16px;")
                slot_layout.addWidget(power_label)
                
                # Nom
                name_label = QLabel("Vide")
                name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                name_label.setWordWrap(True)
                name_label.setStyleSheet("color: white; font-size: 12px;")
                slot_layout.addWidget(name_label)
                
                armor_layout.addWidget(slot)
                self.armor_slots.append(slot)
            
            armor_layout.addStretch()
            logging.info("✅ Colonne de l'armure créée avec succès")
            return armor_layout
            
        except Exception as e:
            logging.error(f"❌ Erreur lors de la création de la colonne de l'armure: {str(e)}")
            logging.exception("Détails de l'erreur:")
            return QVBoxLayout()

    def create_character_widget(self):
        """Crée le widget central du personnage."""
        try:
            logging.info("Création du widget du personnage")
            widget = QWidget()
            layout = QVBoxLayout(widget)
            
            # Niveau de lumière
            power_label = QLabel("LUMIÈRE")
            power_label.setStyleSheet("""
                color: white;
                font-size: 24px;
                font-weight: bold;
            """)
            power_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(power_label)
            
            self.power_value = QLabel("0")
            self.power_value.setStyleSheet("""
                color: #FFEB3B;
                font-size: 48px;
                font-weight: bold;
            """)
            self.power_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.power_value)
            
            # Placeholder pour le personnage
            self.character_view = QLabel()
            self.character_view.setFixedSize(400, 600)
            self.character_view.setStyleSheet("""
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 10px;
                border: 1px solid #3d3f43;
            """)
            layout.addWidget(self.character_view)
            
            logging.info("✅ Widget du personnage créé avec succès")
            return widget
            
        except Exception as e:
            logging.error(f"❌ Erreur lors de la création du widget du personnage: {str(e)}")
            logging.exception("Détails de l'erreur:")
            return QWidget()

    def load_characters(self):
        """Charge la liste des personnages disponibles."""
        try:
            logging.info("=== Chargement des personnages ===")
            
            # Vérifier le fichier account.json
            if not os.path.exists('data/account.json'):
                logging.error("❌ Fichier account.json non trouvé")
                return
            
            # Charger les données du compte
            with open('data/account.json', 'r') as f:
                account_data = json.load(f)
                logging.debug(f"Données du compte chargées")
            
            if not account_data.get('Response'):
                logging.error("❌ Pas de données 'Response' dans account.json")
                return
            
            player_info = account_data['Response'][0]
            membership_id = player_info['membershipId']
            membership_type = player_info['membershipType']
            
            logging.info(f"Chargement des personnages pour membershipId: {membership_id}")
            
            # Requête à l'API Bungie
            headers = {
                'X-API-Key': OAUTH_CONFIG['api_key']
            }
            
            profile_url = f'https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/'
            logging.debug(f"URL de requête: {profile_url}")
            
            response = requests.get(
                profile_url,
                headers=headers,
                params={'components': '200,205'}  # Characters et Equipment components
            )
            
            logging.debug(f"Réponse de l'API: Status {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                characters = data.get('Response', {}).get('characters', {}).get('data', {})
                
                if not characters:
                    logging.error("❌ Aucun personnage trouvé dans les données")
                    return
                
                # Vider le sélecteur
                self.character_selector.clear()
                
                # Classe de personnage mapping
                class_types = {
                    0: "Titan",
                    1: "Chasseur",
                    2: "Arcaniste"
                }
                
                # Trouver le personnage avec la plus haute lumière
                highest_light = 0
                highest_light_char = None
                
                # Ajouter chaque personnage au sélecteur
                for char_id, char_info in characters.items():
                    class_type = class_types.get(char_info.get('classType'), "Inconnu")
                    light_level = char_info.get('light', 0)
                    
                    # Mettre à jour le personnage avec la plus haute lumière
                    if light_level > highest_light:
                        highest_light = light_level
                        highest_light_char = char_info
                    
                    label = f"{class_type} - Lumière {light_level}"
                    logging.info(f"Ajout du personnage: {label} (ID: {char_id})")
                    self.character_selector.addItem(label, char_id)
                
                # Mettre à jour l'affichage de la lumière
                if highest_light_char:
                    self.power_value.setText(str(highest_light))
                    logging.info(f"Lumière mise à jour: {highest_light}")
                
                # Charger le premier personnage
                if self.character_selector.count() > 0:
                    first_char_id = self.character_selector.currentData()
                    self.load_character_equipment(first_char_id)
                    
                    # Mettre à jour la lumière pour le personnage sélectionné
                    char_info = characters.get(first_char_id, {})
                    current_light = char_info.get('light', 0)
                    self.power_value.setText(str(current_light))
                    logging.info(f"Lumière du personnage actuel: {current_light}")
                
            else:
                logging.error(f"❌ Erreur API: {response.status_code}")
                if response.text:
                    logging.error(f"Détails de l'erreur: {response.text}")
                
        except Exception as e:
            logging.error(f"❌ Erreur lors du chargement des personnages: {str(e)}")
            logging.exception("Détails de l'erreur:")

    def load_character_equipment(self, character_id):
        """Charge l'équipement pour un personnage spécifique."""
        try:
            logging.info(f"=== Chargement de l'équipement pour le personnage {character_id} ===")
            
            # Charger les données du compte
            with open('data/account.json', 'r') as f:
                account_data = json.load(f)
            
            player_info = account_data['Response'][0]
            membership_id = player_info['membershipId']
            membership_type = player_info['membershipType']
            
            logging.debug(f"MembershipId: {membership_id}, MembershipType: {membership_type}")
            
            # Requête à l'API
            headers = {
                'X-API-Key': OAUTH_CONFIG['api_key']
            }
            
            equipment_url = f'https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/Character/{character_id}/'
            logging.debug(f"URL de requête équipement: {equipment_url}")
            
            response = requests.get(
                equipment_url,
                headers=headers,
                params={'components': '205,300,302,304,305'}
            )
            
            logging.debug(f"Réponse API équipement: Status {response.status_code}")
            
            if response.status_code == 200:
                equipment_data = response.json()['Response']
                logging.debug(f"Données d'équipement reçues")
                
                character_equipment = equipment_data.get('equipment', {}).get('data', {}).get('items', [])
                instances = equipment_data.get('itemComponents', {}).get('instances', {}).get('data', {})
                
                if not character_equipment:
                    logging.error("❌ Aucun équipement trouvé")
                    return
                
                # Associer les données d'instance à chaque item
                for item in character_equipment:
                    instance_id = item.get('itemInstanceId')
                    if instance_id in instances:
                        item['instance'] = instances[instance_id]
                        logging.debug(f"Item {item.get('itemHash')} - Instance trouvée")
                
                self.display_equipment(character_equipment)
                logging.info("✅ Équipement chargé avec succès")
                
            else:
                logging.error(f"❌ Erreur lors de la récupération de l'équipement: {response.status_code}")
                if response.text:
                    logging.error(f"Détails de l'erreur: {response.text}")
                
        except Exception as e:
            logging.error(f"❌ Erreur lors du chargement de l'équipement: {str(e)}")
            logging.exception("Détails de l'erreur:")

    def display_equipment(self, equipment):
        """Affiche l'équipement dans l'interface."""
        try:
            logging.info("=== Affichage de l'équipement ===")
            
            # Trier l'équipement par type
            sorted_equipment = {
                'weapons': [],
                'armor': []
            }
            
            for item in equipment:
                bucket_hash = str(item.get('bucketHash', ''))
                bucket_type = BUCKET_TYPES.get(bucket_hash, 'unknown')
                
                if bucket_type in ['kinetic', 'energy', 'power']:
                    sorted_equipment['weapons'].append(item)
                    logging.debug(f"Arme trouvée: {item.get('itemHash')}")
                elif bucket_type in ['helmet', 'gauntlets', 'chest', 'legs', 'class_item']:
                    sorted_equipment['armor'].append(item)
                    logging.debug(f"Armure trouvée: {item.get('itemHash')}")
            
            # Mise à jour des slots d'armes
            for i, slot in enumerate(self.weapon_slots):
                if i < len(sorted_equipment['weapons']):
                    self.update_item_display(slot, sorted_equipment['weapons'][i])
            
            # Mise à jour des slots d'armure
            for i, slot in enumerate(self.armor_slots):
                if i < len(sorted_equipment['armor']):
                    self.update_item_display(slot, sorted_equipment['armor'][i])
            
            logging.info(f"✅ Affichage terminé - {len(sorted_equipment['weapons'])} armes, {len(sorted_equipment['armor'])} pièces d'armure")
            
        except Exception as e:
            logging.error(f"❌ Erreur lors de l'affichage de l'équipement: {str(e)}")
            logging.exception("Détails de l'erreur:")

    def update_item_display(self, slot, item):
        """Met à jour l'affichage d'un item dans son slot."""
        try:
            logging.debug(f"Mise à jour du slot pour l'item {item.get('itemHash')}")
            
            # Récupérer les définitions de l'item
            item_hash = str(item.get('itemHash'))
            manifest_url = f"https://www.bungie.net/Platform/Destiny2/Manifest/DestinyInventoryItemDefinition/{item_hash}/"
            
            headers = {
                'X-API-Key': OAUTH_CONFIG['api_key']
            }
            
            response = requests.get(manifest_url, headers=headers)
            
            if response.status_code == 200:
                item_def = response.json()['Response']
                item_name = item_def['displayProperties']['name']
                icon_path = item_def['displayProperties']['icon']
                
                # Télécharger l'icône si nécessaire
                icon_filename = f"icons/{item_hash}.png"
                if not os.path.exists(icon_filename):
                    icon_url = f"https://www.bungie.net{icon_path}"
                    icon_response = requests.get(icon_url)
                    if icon_response.status_code == 200:
                        os.makedirs('icons', exist_ok=True)
                        with open(icon_filename, 'wb') as f:
                            f.write(icon_response.content)
                        logging.debug(f"Icône téléchargée: {icon_filename}")
                
                # Mettre à jour l'interface
                layout = slot.layout()
                if layout:
                    # Icône
                    icon_label = layout.itemAt(0).widget()
                    pixmap = QPixmap(icon_filename)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio)
                        icon_label.setPixmap(scaled_pixmap)
                    
                    # Puissance
                    power = item.get('instance', {}).get('primaryStat', {}).get('value', 0)
                    power_label = layout.itemAt(1).widget()
                    power_label.setText(str(power))
                    
                    # Nom
                    name_label = layout.itemAt(2).widget()
                    name_label.setText(item_name)
                    
                    logging.debug(f"✓ Slot mis à jour - {item_name} ({power})")
                
            else:
                logging.error(f"❌ Erreur lors de la récupération des définitions: {response.status_code}")
            
        except Exception as e:
            logging.error(f"❌ Erreur lors de la mise à jour du slot: {str(e)}")
            logging.exception("Détails de l'erreur:")

    def on_character_changed(self, index):
        """Gère le changement de personnage."""
        try:
            if index >= 0:
                character_id = self.character_selector.currentData()
                logging.info(f"Changement de personnage vers ID: {character_id}")
                
                # Mettre à jour la lumière du nouveau personnage sélectionné
                with open('data/account.json', 'r') as f:
                    account_data = json.load(f)
                
                player_info = account_data['Response'][0]
                membership_id = player_info['membershipId']
                membership_type = player_info['membershipType']
                
                headers = {
                    'X-API-Key': OAUTH_CONFIG['api_key']
                }
                
                profile_url = f'https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/'
                response = requests.get(
                    profile_url,
                    headers=headers,
                    params={'components': '200'}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    characters = data.get('Response', {}).get('characters', {}).get('data', {})
                    char_info = characters.get(character_id, {})
                    light_level = char_info.get('light', 0)
                    
                    # Mettre à jour l'affichage de la lumière
                    self.power_value.setText(str(light_level))
                    logging.info(f"Lumière mise à jour pour le nouveau personnage: {light_level}")
                
                # Charger l'équipement du nouveau personnage
                self.load_character_equipment(character_id)
                
        except Exception as e:
            logging.error(f"❌ Erreur lors du changement de personnage: {str(e)}")

    def refresh_character_data(self):
        """Actualise les données du personnage."""
        try:
            logging.info("=== Actualisation des données du personnage ===")
            self.load_characters()
        except Exception as e:
            logging.error(f"❌ Erreur lors de l'actualisation: {str(e)}")