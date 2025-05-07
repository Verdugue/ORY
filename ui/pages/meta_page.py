from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                         QScrollArea, QFrame, QPushButton, QTabWidget,
                         QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
import requests
from bs4 import BeautifulSoup
import logging
import os
import json
from dotenv import load_dotenv
from utils.config import OAUTH_CONFIG
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random

class ScrapingThread(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def run(self):
        try:
            logging.info("=== Début du scraping des armes meta ===")
            self.progress.emit("Démarrage de la récupération des données...")
            weapons_data = self.get_destinytracker_stats()
            if weapons_data:
                self.finished.emit(weapons_data)
            else:
                raise Exception("Aucune arme n'a pu être récupérée")
        except Exception as e:
            logging.error(f"Erreur critique: {str(e)}")
            self.error.emit("Erreur lors de la récupération des données")

    def get_destinytracker_stats(self):
        try:
            logging.info("=== Début de l'extraction avec authentification manuelle ===")
            self.progress.emit("Configuration du navigateur...")
            
            options = webdriver.ChromeOptions()
            options.add_argument('--start-maximized')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            driver = webdriver.Chrome(options=options)
            
            try:
                # Aller sur la page d'accueil
                self.progress.emit("Accès à light.gg - Veuillez compléter le captcha...")
                driver.get("https://www.light.gg")
                
                # Attendre que l'URL ne contienne plus "challenge"
                while "challenge" in driver.current_url:
                    time.sleep(1)
                    
                # Attendre 5 secondes supplémentaires pour être sûr
                time.sleep(5)
                
                # Maintenant on peut aller sur la page des god rolls
                self.progress.emit("Accès aux données des armes...")
                driver.get("https://www.light.gg/god-roll/")
                
                # Attendre que la page soit chargée
                time.sleep(10)
                
                # Extraction des données
                weapons_data = driver.execute_script("""
                    return Array.from(document.querySelectorAll('.weapon-name')).map(el => ({
                        name: el.textContent.trim(),
                        link: el.href,
                        image: el.querySelector('img')?.src,
                        usage: el.closest('tr')?.querySelector('.usage-percent')?.textContent.trim()
                    }));
                """)
                
                if weapons_data:
                    # Sauvegarder les cookies
                    if not os.path.exists('cache'):
                        os.makedirs('cache')
                    with open('cache/light_gg_cookies.json', 'w') as f:
                        json.dump(driver.get_cookies(), f)
                    
                    return [{
                        'name': weapon['name'],
                        'type': 'Weapon',
                        'image_url': weapon['image'],
                        'usage_rate': weapon.get('usage', 'N/A'),
                        'activity': 'PvE'
                    } for weapon in weapons_data[:10]]
                
            finally:
                driver.quit()
            
            return []
            
        except Exception as e:
            logging.error(f"Erreur critique: {str(e)}")
            return []

    def get_weapon_name(self, item_hash):
        """Récupère le nom de l'arme via l'API Bungie"""
        try:
            url = f'https://www.bungie.net/Platform/Destiny2/Manifest/DestinyInventoryItemDefinition/{item_hash}/'
            headers = {'X-API-Key': OAUTH_CONFIG['api_key']}
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data['Response']['displayProperties']['name']
            return f"Arme {item_hash}"
        except:
            return f"Arme {item_hash}"

class MetaPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.weapons_data = []
        self.image_cache = {}
        self.setup_ui()
        self.load_meta_weapons()  # Charger les données au démarrage

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # En-tête avec titre et bouton refresh
        header = QWidget()
        header_layout = QHBoxLayout(header)
        
        title = QLabel("Top 10 des Armes Meta")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #4d7aff;
                padding: 10px;
            }
        """)
        header_layout.addWidget(title)
        
        refresh_btn = QPushButton("Rafraîchir")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4d7aff;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d6ae8;
            }
        """)
        refresh_btn.clicked.connect(self.load_meta_weapons)
        header_layout.addWidget(refresh_btn)
        header_layout.addStretch()
        
        layout.addWidget(header)

        # Label de chargement
        self.loading_label = QLabel("Chargement des données...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                margin: 20px;
            }
        """)
        layout.addWidget(self.loading_label)
        
        # Tabs pour PvE et PvP
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                background: #1a1a1a;
            }
            QTabBar::tab {
                background: #2d2d2d;
                color: white;
                padding: 8px 15px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                background: #4d7aff;
            }
            QTabBar::tab:hover {
                background: #3d6ae8;
            }
        """)

        # Tab PvE
        self.pve_tab = QWidget()
        self.pve_layout = QVBoxLayout(self.pve_tab)
        self.pve_container = QWidget()
        self.pve_weapons_layout = QVBoxLayout(self.pve_container)
        scroll_pve = QScrollArea()
        scroll_pve.setWidget(self.pve_container)
        scroll_pve.setWidgetResizable(True)
        self.pve_layout.addWidget(scroll_pve)
        self.tabs.addTab(self.pve_tab, "PvE")

        # Tab PvP
        self.pvp_tab = QWidget()
        self.pvp_layout = QVBoxLayout(self.pvp_tab)
        self.pvp_container = QWidget()
        self.pvp_weapons_layout = QVBoxLayout(self.pvp_container)
        scroll_pvp = QScrollArea()
        scroll_pvp.setWidget(self.pvp_container)
        scroll_pvp.setWidgetResizable(True)
        self.pvp_layout.addWidget(scroll_pvp)
        self.tabs.addTab(self.pvp_tab, "PvP")

        layout.addWidget(self.tabs)

    def setup_weapons_container(self, parent_layout):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Label de chargement
        loading_label = QLabel("Chargement des données...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                margin: 20px;
            }
        """)
        layout.addWidget(loading_label)
        
        scroll.setWidget(container)
        parent_layout.addWidget(scroll)
        return layout

    def filter_weapons(self):
        """Filtre les armes selon les critères sélectionnés"""
        activity = self.activity_filter.currentText()
        weapon_type = self.weapon_type_filter.currentText()
        
        filtered_weapons = self.weapons_data.copy()
        
        # Filtrer par activité
        if activity != "Toutes":
            filtered_weapons = [w for w in filtered_weapons if w['activity'] == activity]
            
        # Filtrer par type d'arme
        if weapon_type != "Tous types":
            filtered_weapons = [w for w in filtered_weapons if w['type'] == weapon_type]
            
        # Mettre à jour l'affichage
        self.update_weapons_display(filtered_weapons)

    def update_weapons_display(self, weapons_data):
        """Met à jour l'affichage des armes"""
        try:
            logging.info("=== Mise à jour de l'affichage ===")
            logging.info(f"Nombre d'armes à afficher: {len(weapons_data)}")
            
            # Nettoyer l'affichage existant
            self.loading_label.hide()
            
            # Séparer les armes par type (PvE/PvP)
            pve_weapons = []
            pvp_weapons = []
            
            for weapon in weapons_data:
                if weapon.get('activity') == 'PvP':
                    pvp_weapons.append(weapon)
                else:
                    pve_weapons.append(weapon)
                    
            logging.debug(f"Armes PvE: {len(pve_weapons)}, Armes PvP: {len(pvp_weapons)}")
            
            # Mettre à jour l'onglet PvE
            self.clear_layout(self.pve_weapons_layout)
            for i, weapon in enumerate(pve_weapons, 1):
                try:
                    logging.debug(f"Ajout arme PvE {i}: {weapon.get('name', 'Inconnue')}")
                    weapon_frame = self.create_weapon_frame(i, weapon)
                    self.pve_weapons_layout.addWidget(weapon_frame)
                except Exception as e:
                    logging.error(f"Erreur affichage arme PvE {i}: {str(e)}")
                    continue
            self.pve_weapons_layout.addStretch()
            
            # Mettre à jour l'onglet PvP
            self.clear_layout(self.pvp_weapons_layout)
            for i, weapon in enumerate(pvp_weapons, 1):
                try:
                    logging.debug(f"Ajout arme PvP {i}: {weapon.get('name', 'Inconnue')}")
                    weapon_frame = self.create_weapon_frame(i, weapon)
                    self.pvp_weapons_layout.addWidget(weapon_frame)
                except Exception as e:
                    logging.error(f"Erreur affichage arme PvP {i}: {str(e)}")
                    continue
            self.pvp_weapons_layout.addStretch()
            
            logging.info("Mise à jour de l'affichage terminée")
            
        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour de l'affichage: {str(e)}")
            self.show_error("Erreur d'affichage")

    def clear_layout(self, layout):
        """Nettoie un layout"""
        if layout is None:
            return
        
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def update_tab_weapons(self, tab_layout, weapons):
        """Met à jour l'affichage des armes dans un onglet spécifique"""
        # Nettoyer l'affichage existant
        self.clear_layout(tab_layout)

        # Afficher les armes filtrées
        for i, weapon in enumerate(weapons, 1):
            weapon_frame = self.create_weapon_frame(i, weapon)
            tab_layout.addWidget(weapon_frame)
            
        tab_layout.addStretch()

    def create_weapon_frame(self, rank, weapon):
        """Crée un cadre pour afficher une arme"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 10px;
                padding: 10px;
                margin: 5px;
            }
            QFrame:hover {
                background-color: rgba(0, 0, 0, 0.3);
            }
        """)
        
        layout = QHBoxLayout(frame)
        
        # Rang
        rank_label = QLabel(f"#{rank}")
        rank_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #4d7aff;
                min-width: 40px;
            }
        """)
        layout.addWidget(rank_label)
        
        # Image et nom de l'arme
        weapon_info = QHBoxLayout()
        
        weapon_image = QLabel()
        self.load_image(weapon['image_url'], weapon_image, size=64)
        weapon_info.addWidget(weapon_image)
        
        name_label = QLabel(weapon['name'])
        name_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: white;
                margin-left: 10px;
            }
        """)
        weapon_info.addWidget(name_label)
        
        layout.addLayout(weapon_info)
        
        # Type d'activité et score
        activity_label = QLabel(weapon.get('activity', ''))
        activity_label.setStyleSheet("color: #4d7aff;")
        layout.addWidget(activity_label)
        
        if 'score' in weapon:
            score_label = QLabel(f"Score: {weapon['score']}")
            score_label.setStyleSheet("color: #4d7aff;")
            layout.addWidget(score_label)
        
        layout.addStretch()
        
        return frame

    def load_meta_weapons(self):
        """Lance le chargement des armes meta"""
        self.loading_label.show()
        self.loading_label.setText("Chargement des données...")
        
        self.scraping_thread = ScrapingThread()
        self.scraping_thread.finished.connect(self.update_weapons_display)
        self.scraping_thread.error.connect(self.show_error)
        self.scraping_thread.progress.connect(self.update_progress)
        self.scraping_thread.start()

    def load_image(self, url, label, size=64):
        """Charge une image avec cache en mémoire"""
        try:
            # Vérifier le cache en mémoire
            cache_key = f"{url}_{size}"
            if cache_key in self.image_cache:
                label.setPixmap(self.image_cache[cache_key])
                return

            # Vérifier le cache sur disque
            if not os.path.exists('cache'):
                os.makedirs('cache')
            
            cache_filename = f"cache/{url.split('/')[-1]}"
            
            if not os.path.exists(cache_filename):
                # Si pas dans le cache, télécharger par lots de 5 images maximum
                if len(self.image_cache) % 5 == 0:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        with open(cache_filename, 'wb') as f:
                            f.write(response.content)
                    else:
                        raise Exception(f"Erreur téléchargement: {response.status_code}")
            
            # Charger et redimensionner l'image
            pixmap = QPixmap(cache_filename)
            pixmap = pixmap.scaled(size, size, 
                                 Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation)
            
            # Sauvegarder dans le cache mémoire
            self.image_cache[cache_key] = pixmap
            label.setPixmap(pixmap)
            
        except Exception as e:
            self.logger.error(f"Erreur image {url}: {str(e)}")
            label.setText("!")
            label.setStyleSheet("color: red;")

    def show_error(self, message):
        """Affiche un message d'erreur"""
        self.loading_label.setText(f"Erreur: {message}")
        self.loading_label.setStyleSheet("color: red;")
        self.loading_label.show()

    def update_progress(self, message):
        """Met à jour le message de progression"""
        self.loading_label.setText(message)

    def get_trending_weapons(self):
        """Récupère les armes les plus utilisées via l'API Bungie"""
        try:
            headers = {
                'X-API-Key': OAUTH_CONFIG['api_key']
            }
            
            # Endpoint pour les statistiques d'utilisation
            url = 'https://stats.bungie.net/Platform/Destiny2/Stats/PostGameCarnageReport/'
            
            # Récupérer les données des dernières activités
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                # Analyser les données pour trouver les armes les plus utilisées
                return data
            return None
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des armes trending: {str(e)}")
            return None

    def get_destinytracker_stats(self):
        """Récupère les statistiques depuis l'API Bungie"""
        try:
            logging.info("=== Début de la récupération des stats depuis destinytracker.com ===")
            weapons_data = []
            
            url = 'https://destinytracker.com/destiny-2/db/insights'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html',
                'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
                'Cache-Control': 'no-cache'
            }
            
            session = requests.Session()
            # Faire une première requête à la page d'accueil
            session.get('https://destinytracker.com', headers=headers)
            
            # Attendre un peu avant la requête principale
            time.sleep(2)
            
            logging.info(f"Récupération des armes depuis {url}")
            response = session.get(url, headers=headers, timeout=10)
            logging.debug(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                logging.debug("Page web récupérée, analyse du contenu...")
                
                # Trouver les sections des armes meta
                weapon_sections = soup.find_all('div', {'class': 'weapon-meta-section'})
                
                for section in weapon_sections:
                    activity = 'PvP' if 'pvp' in section.get('class', []) else 'PvE'
                    weapons = section.find_all('div', {'class': 'weapon-item'})
                    
                    for weapon in weapons[:10]:  # Top 10 seulement
                        try:
                            name = weapon.find('div', {'class': 'name'}).text.strip()
                            type_elem = weapon.find('div', {'class': 'type'})
                            weapon_type = type_elem.text.strip() if type_elem else 'Unknown'
                            usage = weapon.find('div', {'class': 'usage'}).text.strip()
                            img = weapon.find('img')
                            image_url = img['src'] if img else ''
                            
                            weapon_data = {
                                'name': name,
                                'type': weapon_type,
                                'image_url': image_url,
                                'usage_rate': usage,
                                'activity': activity
                            }
                            weapons_data.append(weapon_data)
                            logging.debug(f"Arme ajoutée: {name} ({activity})")
                            
                        except Exception as e:
                            logging.error(f"Erreur parsing arme: {str(e)}")
                            continue
                
                if weapons_data:
                    return weapons_data
                
            logging.error(f"Erreur lors de la récupération des données: {response.status_code}")
            return []
            
        except Exception as e:
            logging.error(f"Erreur critique: {str(e)}")
            logging.error("Traceback:", exc_info=True)
            return []