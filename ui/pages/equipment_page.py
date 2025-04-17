from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QComboBox, QPushButton, QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
import logging
import os
import json
import requests
from utils.config import OAUTH_CONFIG, BUCKET_TYPES

class EquipmentPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.weapon_slots = []
        self.armor_slots = []
        
        # Créer le label pour le niveau de puissance
        self.power_value = QLabel("0")
        self.power_value.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #4d7aff;
            }
        """)
        
        self.setup_ui()
        
        # Timer pour l'actualisation automatique (5 minutes)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_character_data)
        self.refresh_timer.start(300000)
        self.load_characters()  # Charger les personnages au démarrage

    def setup_ui(self):
        """Configuration de l'interface utilisateur."""
        layout = QVBoxLayout(self)

        # Header avec sélecteur de personnage et bouton refresh
        header_layout = QHBoxLayout()
        
        self.character_selector = QComboBox()
        self.character_selector.currentIndexChanged.connect(self.change_character)
        header_layout.addWidget(self.character_selector)
        
        refresh_button = QPushButton("Actualiser")
        refresh_button.clicked.connect(self.refresh_character_data)
        header_layout.addWidget(refresh_button)
        
        layout.addLayout(header_layout)
        
        # Layout principal pour l'équipement (3 colonnes)
        equipment_layout = QHBoxLayout()
        
        # Colonne des armes (gauche)
        weapons_group = QGroupBox("Armes")
        weapons_layout = QVBoxLayout()
        self.weapon_slots = self.create_weapons_column()
        for slot in self.weapon_slots:
            weapons_layout.addWidget(slot)
        weapons_group.setLayout(weapons_layout)
        equipment_layout.addWidget(weapons_group)
        
        # Colonne du personnage (centre)
        character_group = QGroupBox("Personnage")
        character_layout = QVBoxLayout()
        
        # Image du personnage
        self.character_icon = QLabel()
        self.character_icon.setFixedSize(200, 200)
        self.character_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        character_layout.addWidget(self.character_icon)
        
        # Niveau de lumière du personnage
        self.character_light = QLabel("0")
        self.character_light.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.character_light.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #4d7aff;
            }
        """)
        character_layout.addWidget(self.character_light)
        
        character_group.setLayout(character_layout)
        equipment_layout.addWidget(character_group)
        
        # Colonne de l'armure (droite)
        armor_group = QGroupBox("Armure")
        armor_layout = QVBoxLayout()
        self.armor_slots = self.create_armor_column()
        for slot in self.armor_slots:
            armor_layout.addWidget(slot)
        armor_group.setLayout(armor_layout)
        equipment_layout.addWidget(armor_group)
        
        layout.addLayout(equipment_layout)

    def create_weapons_column(self):
        """Crée les slots pour les armes."""
        slots = []
        weapon_types = ['Cinétique', 'Énergie', 'Puissance']
        
        for weapon_type in weapon_types:
            slot = QWidget()
            slot_layout = QHBoxLayout()
            
            # Icône
            slot.icon_label = QLabel()
            slot.icon_label.setFixedSize(50, 50)
            slot.icon_label.setStyleSheet("background-color: rgba(0, 0, 0, 0.3); border-radius: 5px;")
            slot_layout.addWidget(slot.icon_label)
            
            # Informations
            info_layout = QVBoxLayout()
            slot.name_label = QLabel(weapon_type)
            slot.name_label.setStyleSheet("color: #ffffff; font-weight: bold;")
            slot.power_label = QLabel("0")
            slot.power_label.setStyleSheet("color: #4d7aff; font-weight: bold;")
            info_layout.addWidget(slot.name_label)
            info_layout.addWidget(slot.power_label)
            slot_layout.addLayout(info_layout)
            
            slot.setLayout(slot_layout)
            slots.append(slot)
        
        return slots

    def create_armor_column(self):
        """Crée les slots pour l'armure."""
        slots = []
        armor_types = ['Casque', 'Gants', 'Torse', 'Jambes', 'Marque de classe']
            
        for armor_type in armor_types:
            slot = QWidget()
            slot_layout = QHBoxLayout()
            
            # Icône
            slot.icon_label = QLabel()
            slot.icon_label.setFixedSize(50, 50)
            slot.icon_label.setStyleSheet("background-color: rgba(0, 0, 0, 0.3); border-radius: 5px;")
            slot_layout.addWidget(slot.icon_label)
            
            # Informations
            info_layout = QVBoxLayout()
            slot.name_label = QLabel(armor_type)
            slot.name_label.setStyleSheet("color: #ffffff; font-weight: bold;")
            slot.power_label = QLabel("0")
            slot.power_label.setStyleSheet("color: #4d7aff; font-weight: bold;")
            info_layout.addWidget(slot.name_label)
            info_layout.addWidget(slot.power_label)
            slot_layout.addLayout(info_layout)
            
            slot.setLayout(slot_layout)
            slots.append(slot)
        
        return slots

    def load_characters(self):
        """Charge la liste des personnages disponibles."""
        try:
            self.logger.info("=== Chargement des personnages ===")
            
            if not os.path.exists('data/account.json'):
                self.logger.error("❌ Fichier account.json non trouvé")
                return
            
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
                params={'components': '200,205'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'Response' in data and 'characters' in data['Response']:
                    characters = data['Response']['characters']['data']
                    
                    # Sauvegarder les données complètes
                    with open('data/full_account.json', 'w') as f:
                        json.dump(data, f, indent=4)
                    
                    # Mettre à jour le sélecteur de personnage
                    self.character_selector.clear()
                    for char_id, char_data in characters.items():
                        class_type = self.get_class_type(char_data['classType'])
                        light_level = char_data['light']
                        self.character_selector.addItem(f"{class_type} - {light_level}", char_id)
                
                # Charger le premier personnage
                if self.character_selector.count() > 0:
                    self.load_character_equipment(self.character_selector.currentData())
                
            else:
                self.logger.error(f"Erreur API: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des personnages: {str(e)}")
            self.logger.exception("Détails de l'erreur:")

    def load_character_equipment(self, character_id):
        """Charge l'équipement pour un personnage spécifique."""
        try:
            self.logger.info(f"=== Chargement de l'équipement pour le personnage {character_id} ===")
            
            # Charger les données du compte
            if not os.path.exists('data/account.json'):
                self.logger.error("❌ Données du compte non trouvées")
                return

            with open('data/account.json', 'r') as f:
                account_data = json.load(f)
            
            player_info = account_data['Response'][0]
            membership_id = player_info['membershipId']
            membership_type = player_info['membershipType']
            
            headers = {
                'X-API-Key': OAUTH_CONFIG['api_key']
            }
            
            # Un seul appel API pour obtenir l'équipement et les instances
            equipment_url = f'https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/Character/{character_id}/'
            response = requests.get(
                equipment_url,
                headers=headers,
                params={'components': '205,300,302'}  # Réduit le nombre de composants demandés
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'Response' in data:
                    equipment = data['Response']['equipment']['data']['items']
                    instances = data['Response']['itemComponents']['instances']['data']
                    
                    # Mettre à jour les niveaux de lumière
                    for item in equipment:
                        instance_id = item.get('itemInstanceId')
                        if instance_id and instance_id in instances:
                            instance_data = instances[instance_id]
                            item['light'] = instance_data.get('primaryStat', {}).get('value', 0)
                    
                    # Mettre à jour l'affichage
                    self.display_equipment(equipment)
                else:
                    self.logger.error("Structure de données inattendue dans la réponse")
            else:
                self.logger.error(f"Erreur API: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de l'équipement: {str(e)}")
            self.logger.exception("Détails de l'erreur:")

    def display_equipment(self, equipment):
        """Affiche l'équipement dans l'interface."""
        try:
            self.logger.info("=== Affichage de l'équipement ===")
            
            weapons = []
            armor = []
            
            for item in equipment:
                bucket_hash = str(item.get('bucketHash'))
                bucket_type = self.get_bucket_type(bucket_hash)
                
                if bucket_type in ['kinetic', 'energy', 'power']:
                    weapons.append(item)
                elif bucket_type in ['helmet', 'gauntlets', 'chest', 'legs', 'class_item']:
                    armor.append(item)
            
            # Mettre à jour les armes
            for i, weapon in enumerate(weapons):
                if i < len(self.weapon_slots):
                    slot = self.weapon_slots[i]
                    light = weapon.get('light', 0)
                    item_hash = str(weapon.get('itemHash'))
                    
                    if hasattr(slot, 'power_label'):
                        slot.power_label.setText(str(light))
                    
                    if hasattr(slot, 'icon_label'):
                        icon_path = f'icons/{item_hash}.png'
                        if os.path.exists(icon_path):
                            pixmap = QPixmap(icon_path)
                            if not pixmap.isNull():
                                scaled_pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio)
                                slot.icon_label.setPixmap(scaled_pixmap)
            
            # Mettre à jour l'armure
            for i, armor_piece in enumerate(armor):
                if i < len(self.armor_slots):
                    slot = self.armor_slots[i]
                    light = armor_piece.get('light', 0)
                    item_hash = str(armor_piece.get('itemHash'))
                    
                    if hasattr(slot, 'power_label'):
                        slot.power_label.setText(str(light))
                    
                    if hasattr(slot, 'icon_label'):
                        icon_path = f'icons/{item_hash}.png'
                        if os.path.exists(icon_path):
                            pixmap = QPixmap(icon_path)
                            if not pixmap.isNull():
                                scaled_pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio)
                                slot.icon_label.setPixmap(scaled_pixmap)
            
            self.logger.info(f"Affichage terminé - {len(weapons)} armes, {len(armor)} pièces d'armure")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'affichage de l'équipement: {str(e)}")

    def change_character(self, index):
        """Appelé lorsqu'un nouveau personnage est sélectionné."""
        if index >= 0:
            character_id = self.character_selector.currentData()
            self.logger.info(f"Changement de personnage vers ID: {character_id}")
            
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
                self.character_light.setText(str(light_level))
                self.logger.info(f"Lumière mise à jour pour le nouveau personnage: {light_level}")
            
            # Charger l'équipement du nouveau personnage
            self.load_character_equipment(character_id)

    def refresh_character_data(self):
        """Actualise les données du personnage depuis l'API."""
        try:
            self.logger.info("=== Actualisation des données du personnage ===")
            self.load_characters()
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'actualisation: {str(e)}")
            QMessageBox.warning(self, "Erreur", f"Impossible d'actualiser les données: {str(e)}")

    def get_class_type(self, class_type):
        """Convertit le type de classe en texte."""
        classes = {
            0: "Titan",
            1: "Chasseur",
            2: "Arcaniste"
        }
        return classes.get(class_type, "Inconnu")

    def get_bucket_type(self, bucket_hash):
        """Retourne le type d'emplacement d'équipement basé sur le bucket hash."""
        bucket_types = {
            '1498876634': 'kinetic',    # Arme cinétique
            '2465295065': 'energy',     # Arme énergétique
            '953998645': 'power',       # Arme lourde
            '3448274439': 'helmet',     # Casque
            '3551918588': 'gauntlets',  # Gants
            '14239492': 'chest',        # Torse
            '20886954': 'legs',         # Jambes
            '1585787867': 'class_item', # Objet de classe
        }
        return bucket_types.get(bucket_hash, 'unknown')