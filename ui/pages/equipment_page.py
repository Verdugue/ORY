from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QComboBox, QPushButton, QGroupBox, QMessageBox, QDialog, QFrame,
                           QApplication, QProgressBar, QStackedLayout, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QPixmap, QIcon, QMovie
import logging
import os
import json
import requests
from functools import partial
from utils.config import OAUTH_CONFIG, BUCKET_TYPES
from urllib.parse import urlparse, parse_qs

class EquipmentSlot(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("equipmentSlot")  # Pour le style ciblé
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton#equipmentSlot {
                background: #232a3a;
                border: 2px solid #4d7aff;
                border-radius: 12px;
                padding: 8px;
                margin: 8px 0;
                min-width: 180px;
                min-height: 80px;
                text-align: left;
                color: #fff;
                font-size: 16px;
            }
            QPushButton#equipmentSlot:hover {
                background: #2e3650;
                border: 2px solid #ffd700;
                color: #ffd700;
            }
        """)
        self.setFlat(False)
        self.item = None
        self.clicked.connect(lambda: print("Clic sur le slot !"))  # Debug visuel

    def set_item(self, item):
        self.item = item
        if item:
            # Compose le texte du bouton (nom, lumière, etc.) SANS HTML
            name = item.get('name', str(item.get('itemHash', '')))
            light = item.get('light', '')
            text = f"{light}\n{name}"
            self.setText(text)
            # Ajoute l'icône à gauche
            icon_path = f'icons/{item.get("itemHash")}.png'
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                self.setIcon(QIcon(pixmap))
                self.setIconSize(QSize(50, 50))
        else:
            self.setText("")
            self.setIcon(QIcon())

class EquipmentPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.weapon_slots = []
        self.armor_slots = []
        self.power_value = QLabel("0")
        self.power_value.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #4d7aff;
            }
        """)
        # Utilise un QStackedLayout pour alterner entre la vue principale et la vue détail
        self.stacked_layout = QStackedLayout(self)
        self.main_widget = QWidget()
        self.detail_widget = None  # Créé dynamiquement
        self.setup_ui(self.main_widget)
        self.stacked_layout.addWidget(self.main_widget)
        self.init_loading_bar()
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_character_data)
        self.refresh_timer.start(300000)
        self.load_characters()

    def init_loading_bar(self):
        self.loading_bar = QProgressBar(self)
        self.loading_bar.setRange(0, 100)
        self.loading_bar.setValue(0)
        self.loading_bar.setStyleSheet("QProgressBar { text-align: center; }")
        self.loading_bar.hide()
        self.stacked_layout.addWidget(self.loading_bar)

    def setup_ui(self, parent_widget):
        layout = QVBoxLayout(parent_widget)

        # Si aucun compte n'est enregistré, afficher un message d'aide
        if not os.path.exists('data/account.json'):
            empty_label = QLabel("Aucun compte Destiny 2 enregistré.\nEnregistrez un compte dans l'onglet Compte.")
            empty_label.setStyleSheet("color: #ff4444; font-size: 18px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty_label)
            return

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
        """Crée les slots pour les armes et retourne une liste de slots."""
        slots = []
        for weapon_type in ['kinetic', 'energy', 'power']:
            slot = EquipmentSlot()
            slot.clicked.connect(lambda _, s=slot: self.open_equipment_details(s.item) if s.item else None)
            slots.append(slot)
        return slots

    def create_armor_column(self):
        """Crée les slots pour l'armure et retourne une liste de slots."""
        slots = []
        armor_types = ['Casque', 'Gants', 'Torse', 'Jambes', 'Marque de classe']
        for armor_type in armor_types:
            slot = EquipmentSlot()
            slot.clicked.connect(lambda _, s=slot: self.open_equipment_details(s.item) if s.item else None)
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
            # Ajoute le composant 304 pour récupérer les stats d'instance
            equipment_url = f'https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/Character/{character_id}/'
            response = requests.get(
                equipment_url,
                headers=headers,
                params={'components': '205,300,302,304'}
            )
            if response.status_code == 200:
                data = response.json()
                if 'Response' in data:
                    equipment = data['Response']['equipment']['data']['items']
                    instances = data['Response']['itemComponents']['instances']['data']
                    stats_data = data['Response']['itemComponents'].get('stats', {}).get('data', {})
                    # Mettre à jour les niveaux de lumière et les stats réelles
                    for item in equipment:
                        instance_id = item.get('itemInstanceId')
                        if instance_id and instance_id in instances:
                            instance_data = instances[instance_id]
                            item['light'] = instance_data.get('primaryStat', {}).get('value', 0)
                        # Ajout : stats réelles de l'arme du joueur
                        if instance_id and instance_id in stats_data:
                            item['stats'] = {stat_hash: stat_obj['value'] for stat_hash, stat_obj in stats_data[instance_id]['stats'].items()}
                        else:
                            item['stats'] = {}
                    # Mettre à jour l'affichage
                    self.display_equipment(equipment)
                else:
                    self.logger.error("Structure de données inattendue dans la réponse")
            elif response.status_code == 503:
                QMessageBox.warning(self, "Erreur Bungie", "L'API Bungie est temporairement indisponible (503). Réessaie dans quelques minutes.")
            else:
                self.logger.error(f"Erreur API: {response.status_code}")
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de l'équipement: {str(e)}")
            self.logger.exception("Détails de l'erreur:")
            raise

    def display_equipment(self, equipment):
        """Affiche l'équipement dans l'interface."""
        try:
            self.logger.info("=== Affichage de l'équipement ===")
            
            weapons = []
            armor = []
            power_values = []

            for item in equipment:
                bucket_hash = str(item.get('bucketHash'))
                bucket_type = self.get_bucket_type(bucket_hash)
                
                if bucket_type in ['kinetic', 'energy', 'power']:
                    weapons.append(item)
                elif bucket_type in ['helmet', 'gauntlets', 'chest', 'legs', 'class_item']:
                    armor.append(item)
                
                # Ajout pour calculer la lumière réelle
                if 'light' in item and item['light']:
                    power_values.append(item['light'])
            
            # Mettre à jour les armes
            weapon_types = ['kinetic', 'energy', 'power']
            for idx, wtype in enumerate(weapon_types):
                weapon = next((item for item in weapons if self.get_bucket_type(str(item.get('bucketHash'))) == wtype), None)
                if idx < len(self.weapon_slots):
                    slot = self.weapon_slots[idx]
                    self.update_equipment_slot(slot, weapon)
            
            # Mettre à jour l'armure
            armor_types = ['helmet', 'gauntlets', 'chest', 'legs', 'class_item']
            for idx, atype in enumerate(armor_types):
                armor_piece = next((item for item in armor if self.get_bucket_type(str(item.get('bucketHash'))) == atype), None)
                if idx < len(self.armor_slots):
                    slot = self.armor_slots[idx]
                    self.update_equipment_slot(slot, armor_piece)           
            # === NOUVEAU : Calcul et affichage de la lumière réelle ===
            if power_values:
                real_light = int(sum(power_values) / len(power_values))
                self.character_light.setText(str(real_light))
            else:
                self.character_light.setText("???")
            
            # À la fin, afficher la lumière officielle si elle existe
            if hasattr(self, 'current_official_light'):
                self.character_light.setText(str(self.current_official_light))
            else:
                self.character_light.setText("???")
            
            self.logger.info(f"Affichage terminé - {len(weapons)} armes, {len(armor)} pièces d'armure")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'affichage de l'équipement: {str(e)}")

    def show_loading(self, message=""):
        self.loading_bar.show()
        self.loading_bar.setValue(0)
        self.loading_bar.setFormat(message)
        QApplication.processEvents()

    def hide_loading(self):
        self.loading_bar.hide()
        QApplication.processEvents()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'loading_bar') and self.loading_bar:
            self.loading_bar.setGeometry(0, 0, self.width(), self.height())

    def change_character(self, index):
        """Appelé lorsqu'un nouveau personnage est sélectionné."""
        if index >= 0:
            self.show_loading("Chargement du personnage...")
            character_id = self.character_selector.currentData()
            self.logger.info(f"Changement de personnage vers ID: {character_id}")
            try:
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
                    # Stocker la lumière officielle pour l'affichage
                    self.current_official_light = light_level
                    self.character_light.setText(str(light_level))
                    self.logger.info(f"Lumière mise à jour pour le nouveau personnage: {light_level}")
                # Charger l'équipement du nouveau personnage
                self.load_character_equipment(character_id)
            except Exception as e:
                self.logger.error(f"Erreur lors du changement de personnage: {str(e)}")
                QMessageBox.warning(self, "Erreur", f"Impossible de charger le personnage: {str(e)}")
            finally:
                self.hide_loading()

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

    def open_equipment_details(self, item):
        if not item:
            self.logger.warning("open_equipment_details appelé sans item !")
            return
        self.logger.info(f"Ouverture des détails pour l'item : {item.get('name', item.get('itemHash'))}")
        # Nettoyage de l'ancienne page de détail
        if self.detail_widget:
            self.logger.debug("Suppression de l'ancien widget de détail.")
            self.stacked_layout.removeWidget(self.detail_widget)
            self.detail_widget.deleteLater()
        # Choix du template
        try:
            if item.get('inventory', {}).get('tierTypeName', '').lower() == 'exotique' or item.get('inventory', {}).get('tierType') == 6:
                self.logger.info("Affichage du template exotique.")
                self.detail_widget = self.create_exotic_weapon_detail(item)
            else:
                self.logger.info("Affichage du template non-exotique.")
                self.detail_widget = self.create_non_exotic_weapon_detail(item)
            self.stacked_layout.addWidget(self.detail_widget)
            self.stacked_layout.setCurrentWidget(self.detail_widget)
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ouverture des détails : {e}")
            import traceback; self.logger.error(traceback.format_exc())

    def show_main_page(self):
        self.stacked_layout.setCurrentWidget(self.main_widget)
        if self.detail_widget:
            self.stacked_layout.removeWidget(self.detail_widget)
            self.detail_widget.deleteLater()
            self.detail_widget = None

    def update_equipment_slot(self, slot, item):
        """Met à jour le slot d'équipement avec les infos de l'API Manifest."""
        try:
            if not item:
                slot.set_item(None)
                return
            item_hash = str(item.get('itemHash', ''))
            # Récupérer les infos de l'API Manifest
            headers = {
                'X-API-Key': OAUTH_CONFIG['api_key'],
                'Content-Type': 'application/json'
            }
            manifest_url = f"https://www.bungie.net/Platform/Destiny2/Manifest/DestinyInventoryItemDefinition/{item_hash}/"
            response = requests.get(manifest_url, headers=headers)
            if response.status_code == 200:
                item_def = response.json()['Response']
                item_name = item_def['displayProperties']['name']
                icon_path = item_def['displayProperties']['icon']
                icon_url = f"https://www.bungie.net{icon_path}"
                # Télécharger l'icône si besoin
                icon_filename = f"icons/{item_hash}.png"
                if not os.path.exists(icon_filename) or os.path.getsize(icon_filename) == 0:
                    icon_response = requests.get(icon_url)
                    if icon_response.status_code == 200:
                        with open(icon_filename, 'wb') as f:
                            f.write(icon_response.content)
                # Mettre à jour l'item avec le nom
                item['name'] = item_name
                slot.set_item(item)

                # Type de munition
                ammo_type_map = {1: "Primaire", 2: "Spéciale", 3: "Lourde"}
                ammo_type_icon_map = {
                    1: "icons/ammo_primary.png",
                    2: "icons/ammo_special.png",
                    3: "icons/ammo_heavy.png"
                }
                ammo_type = item_def.get("equippingBlock", {}).get("ammoType", 0)
                item["ammoType"] = ammo_type_map.get(ammo_type, "Inconnu")
                item["ammoTypeIcon"] = ammo_type_icon_map.get(ammo_type, "")

                # Énergie
                energy_type_map = {0: "Aucune", 1: "Arc", 2: "Solaire", 3: "Cryo-électrique", 4: "Stasique", 6: "Strand"}
                energy_type_icon_map = {
                    1: "icons/energy_arc.png",
                    2: "icons/energy_solar.png",
                    3: "icons/energy_void.png",
                    4: "icons/energy_stasis.png",
                    6: "icons/energy_strand.png"
                }
                energy = item_def.get("energy", {})
                if energy:
                    energy_type = energy.get("energyType", 0)
                    item["energy"] = energy_type_map.get(energy_type, "Aucune")
                    item["energyIcon"] = energy_type_icon_map.get(energy_type, "")
                else:
                    item["energy"] = "Cinétique"
                    item["energyIcon"] = "icons/energy_kinetic.png"

                # Statistiques (récupère aussi l'icône)
                item['stats'] = {}
                if 'stats' in item_def and 'stats' in item_def['stats']:
                    for stat_hash, stat_obj in item_def['stats']['stats'].items():
                        # Récupère le nom et l'icône du stat via DestinyStatDefinition
                        stat_info = self.get_stat_info(stat_hash)
                        item['stats'][stat_hash] = {
                            "value": stat_obj.get('value', 0),
                            "name": stat_info.get("name", str(stat_hash)),
                            "icon": stat_info.get("icon", "")
                        }

                # Pour les perks
                item['perks'] = []
                if 'perks' in item_def:
                    for perk in item_def['perks'].get('perkHashes', []):
                        item['perks'].append(str(perk))

                # Pour les sockets
                item['sockets'] = []
                if 'sockets' in item_def:
                    for socket in item_def['sockets'].get('socketEntries', []):
                        item['sockets'].append(str(socket.get('singleInitialItemHash', '')))
            else:
                slot.set_item(item)  # Affiche au moins la lumière et le hash
        except Exception as e:
            logging.error(f"Erreur update_equipment_slot: {str(e)}")
            slot.set_item(item)

    def get_stat_info(self, stat_hash, lang="fr"):
        try:
            headers = {
                'X-API-Key': OAUTH_CONFIG['api_key'],
                'Content-Type': 'application/json'
            }
            url = f"https://www.bungie.net/Platform/Destiny2/Manifest/DestinyStatDefinition/{stat_hash}/"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                display = data['Response']['displayProperties']
                icon_path = display.get("icon", "")
                if icon_path:
                    # Télécharger et sauvegarder l'icône localement
                    icon_url = f"https://www.bungie.net{icon_path}"
                    icon_filename = f"icons/stat_{stat_hash}.png"
                    if not os.path.exists(icon_filename) or os.path.getsize(icon_filename) == 0:
                        icon_response = requests.get(icon_url)
                        if icon_response.status_code == 200:
                            with open(icon_filename, 'wb') as f:
                                f.write(icon_response.content)
                    return {
                        "name": display.get("name", str(stat_hash)),
                        "icon": icon_filename
                    }
        except Exception as e:
            logging.error(f"Erreur get_stat_info: {e}")
        return {"name": str(stat_hash), "icon": ""}

    def create_non_exotic_weapon_detail(self, item):
        self.logger.debug(f"Création du widget détail non-exotique pour : {item.get('name', item.get('itemHash'))}")
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # En-tête avec bouton retour
        header = QHBoxLayout()
        back_btn = QPushButton("← Retour")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #4d7aff;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5d8aff;
            }
        """)
        back_btn.clicked.connect(self.show_main_page)
        header.addWidget(back_btn)
        header.addStretch()
        layout.addLayout(header)

        # Section principale horizontale
        main_section = QHBoxLayout()

        # Colonne gauche : image + type de munition + énergie
        left_col = QVBoxLayout()
        icon_path = f"icons/{item.get('itemHash')}.png"
        img = QLabel()
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            img.setPixmap(pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_col.addWidget(img)
        # Type de munition (gras)
        ammo = item.get('ammoType', '')
        ammo_label = QLabel(f"{ammo}")
        ammo_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        left_col.addWidget(ammo_label, alignment=Qt.AlignmentFlag.AlignLeft)
        # Énergie (normal)
        energy = item.get('energy', '')
        energy_label = QLabel(f"{energy}")
        energy_label.setStyleSheet("font-size: 14px;")
        left_col.addWidget(energy_label, alignment=Qt.AlignmentFlag.AlignLeft)
        left_col.addStretch()
        main_section.addLayout(left_col)

        # Colonne droite : nom, perk, stats
        right_col = QVBoxLayout()
        # Nom de l'arme
        name_label = QLabel(item.get('name', ''))
        name_label.setStyleSheet("color: #4d7aff; font-size: 28px; font-weight: bold;")
        right_col.addWidget(name_label)
        # Perk de base (gros, encadré)
        perks = item.get('perks', [])
        if perks:
            perk_label = QLabel(perks[0])
            perk_label.setStyleSheet("border: 2px solid #4d7aff; border-radius: 6px; padding: 10px; font-size: 18px; font-weight: bold; background: #232a3a;")
            right_col.addWidget(perk_label)
        # Statistiques (encadré)
        stats = item.get('stats', {})
        # Filtrer et trier les stats
        filtered_stats = {k: v for k, v in stats.items() if v != 0 and isinstance(v, dict) and "value" in v}
        sorted_stats = dict(sorted(filtered_stats.items(), key=lambda x: x[1]["value"], reverse=True))
        if sorted_stats:
            stats_group = QGroupBox("Statistiques")
            stats_group.setStyleSheet("""
                QGroupBox {
                    border: 2px solid #4d7aff;
                    border-radius: 8px;
                    margin-top: 1em;
                    padding: 15px;
                    background-color: rgba(35, 37, 41, 0.7);
                }
                QGroupBox::title {
                    color: #4d7aff;
                    font-weight: bold;
                    font-size: 16px;
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
            """)
            stats_layout = QVBoxLayout()
            stats_layout.setSpacing(8)
            for stat_hash, stat_data in sorted_stats.items():
                stat_name = stat_data["name"]
                stat_value = stat_data["value"]
                stat_row = QHBoxLayout()
                stat_row.setSpacing(10)
                
                # Conteneur pour la stat
                stat_container = QFrame()
                stat_container.setStyleSheet("""
                    QFrame {
                        background-color: rgba(77, 122, 255, 0.1);
                        border-radius: 6px;
                        padding: 8px;
                    }
                """)
                stat_container_layout = QHBoxLayout(stat_container)
                stat_container_layout.setContentsMargins(8, 4, 8, 4)
                
                # Nom de la stat
                name_label = QLabel(stat_name)
                name_label.setStyleSheet("""
                    color: #ffffff;
                    font-size: 14px;
                    font-weight: bold;
                """)
                stat_container_layout.addWidget(name_label)
                
                # Valeur de la stat
                value_label = QLabel(str(stat_value))
                value_label.setStyleSheet("""
                    color: #4d7aff;
                    font-size: 14px;
                    font-weight: bold;
                    padding-left: 10px;
                """)
                value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                stat_container_layout.addWidget(value_label)
                
                stat_row.addWidget(stat_container)
                stats_layout.addLayout(stat_row)
            stats_group.setLayout(stats_layout)
            right_col.addWidget(stats_group)
        right_col.addStretch()
        main_section.addLayout(right_col)

        layout.addLayout(main_section)
        layout.addStretch()
        return widget

    def create_exotic_weapon_detail(self, item):
        # Même structure que non-exotique, mais nom en doré et perk exotique si dispo
        self.logger.debug(f"Création du widget détail exotique pour : {item.get('name', item.get('itemHash'))}")
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # En-tête avec bouton retour
        header = QHBoxLayout()
        back_btn = QPushButton("← Retour")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #4d7aff;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5d8aff;
            }
        """)
        back_btn.clicked.connect(self.show_main_page)
        header.addWidget(back_btn)
        header.addStretch()
        layout.addLayout(header)

        # Section principale horizontale
        main_section = QHBoxLayout()

        # Colonne gauche : image + type de munition + énergie
        left_col = QVBoxLayout()
        icon_path = f"icons/{item.get('itemHash')}.png"
        img = QLabel()
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            img.setPixmap(pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_col.addWidget(img)
        # Type de munition (gras)
        ammo = item.get('ammoType', '')
        ammo_label = QLabel(f"{ammo}")
        ammo_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        left_col.addWidget(ammo_label, alignment=Qt.AlignmentFlag.AlignLeft)
        # Énergie (normal)
        energy = item.get('energy', '')
        energy_label = QLabel(f"{energy}")
        energy_label.setStyleSheet("font-size: 14px;")
        left_col.addWidget(energy_label, alignment=Qt.AlignmentFlag.AlignLeft)
        left_col.addStretch()
        main_section.addLayout(left_col)

        # Colonne droite : nom, perk, stats
        right_col = QVBoxLayout()
        # Nom de l'arme (doré)
        name_label = QLabel(item.get('name', ''))
        name_label.setStyleSheet("color: #ffd700; font-size: 28px; font-weight: bold;")
        right_col.addWidget(name_label)
        # Perk exotique (gros, encadré)
        perks = item.get('perks', [])
        if perks:
            perk_label = QLabel(perks[0])
            perk_label.setStyleSheet("border: 2px solid #ffd700; border-radius: 6px; padding: 10px; font-size: 18px; font-weight: bold; background: #232a3a;")
            right_col.addWidget(perk_label)
        # Statistiques (encadré)
        stats = item.get('stats', {})
        # Filtrer et trier les stats
        filtered_stats = {k: v for k, v in stats.items() if v != 0 and isinstance(v, dict) and "value" in v}
        sorted_stats = dict(sorted(filtered_stats.items(), key=lambda x: x[1]["value"], reverse=True))
        if sorted_stats:
            stats_group = QGroupBox("Statistiques")
            stats_group.setStyleSheet("""
                QGroupBox {
                    border: 2px solid #ffd700;
                    border-radius: 8px;
                    margin-top: 1em;
                    padding: 15px;
                    background-color: rgba(35, 37, 41, 0.7);
                }
                QGroupBox::title {
                    color: #ffd700;
                    font-weight: bold;
                    font-size: 16px;
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
            """)
            stats_layout = QVBoxLayout()
            stats_layout.setSpacing(8)
            for stat_hash, stat_data in sorted_stats.items():
                stat_name = stat_data["name"]
                stat_value = stat_data["value"]
                stat_row = QHBoxLayout()
                stat_row.setSpacing(10)
                
                # Conteneur pour la stat
                stat_container = QFrame()
                stat_container.setStyleSheet("""
                    QFrame {
                        background-color: rgba(255, 215, 0, 0.1);
                        border-radius: 6px;
                        padding: 8px;
                    }
                """)
                stat_container_layout = QHBoxLayout(stat_container)
                stat_container_layout.setContentsMargins(8, 4, 8, 4)
                
                # Nom de la stat
                name_label = QLabel(stat_name)
                name_label.setStyleSheet("""
                    color: #ffffff;
                    font-size: 14px;
                    font-weight: bold;
                """)
                stat_container_layout.addWidget(name_label)
                
                # Valeur de la stat
                value_label = QLabel(str(stat_value))
                value_label.setStyleSheet("""
                    color: #ffd700;
                    font-size: 14px;
                    font-weight: bold;
                    padding-left: 10px;
                """)
                value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                stat_container_layout.addWidget(value_label)
                
                stat_row.addWidget(stat_container)
                stats_layout.addLayout(stat_row)
            stats_group.setLayout(stats_layout)
            right_col.addWidget(stats_group)
        right_col.addStretch()
        main_section.addLayout(right_col)

        layout.addLayout(main_section)
        layout.addStretch()
        return widget