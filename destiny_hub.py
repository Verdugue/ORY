# Imports actuels dupliqués
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                          QHBoxLayout, QPushButton, QLineEdit, QLabel, 
                          QStackedWidget, QTextEdit, QMessageBox, QTableWidget, 
                          QTableWidgetItem, QHeaderView, QSplitter, QPlainTextEdit, 
                          QInputDialog, QGroupBox, QProgressDialog, QTabWidget, 
                          QComboBox, QGridLayout, QListWidget, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, QMetaObject, Q_ARG, pyqtSlot
from PyQt6.QtGui import QFont, QPalette, QColor, QPixmap, QIcon
import sys
import requests
import json
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import webbrowser
from urllib.parse import urlencode
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import socket
import psutil

# Load environment variables
load_dotenv()

# Configurez le logging après les imports
logging.basicConfig(
    filename='destiny_hub.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ErrorLogHandler(logging.Handler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def emit(self, record):
        self.callback(record)

class ErrorLogWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Créer un splitter pour diviser la vue
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        # Table pour la liste des erreurs
        self.error_table = QTableWidget()
        self.error_table.setColumnCount(4)
        self.error_table.setHorizontalHeaderLabels(['Timestamp', 'Level', 'Source', 'Message'])
        self.error_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.error_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.error_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        splitter.addWidget(self.error_table)

        # Zone de détails pour l'erreur sélectionnée
        self.error_details = QPlainTextEdit()
        self.error_details.setReadOnly(True)
        splitter.addWidget(self.error_details)

        # Boutons de contrôle
        button_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Clear Logs")
        self.clear_btn.clicked.connect(self.clear_logs)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_logs)
        
        self.auto_refresh = QPushButton("Auto Refresh: Off")
        self.auto_refresh.setCheckable(True)
        self.auto_refresh.clicked.connect(self.toggle_auto_refresh)
        
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.auto_refresh)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)

        # Connecter la sélection de la table aux détails
        self.error_table.itemSelectionChanged.connect(self.show_error_details)

        # Timer pour l'auto-refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_logs)

        # Charger les logs initiaux
        self.refresh_logs()

    def clear_logs(self):
        try:
            with open('destiny_hub.log', 'w') as f:
                f.write('')
            self.refresh_logs()
            logging.info("Logs cleared successfully")
        except Exception as e:
            logging.error(f"Failed to clear logs: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to clear logs: {str(e)}")

    def toggle_auto_refresh(self):
        if self.auto_refresh.isChecked():
            self.auto_refresh.setText("Auto Refresh: On")
            self.refresh_timer.start(5000)  # Refresh every 5 seconds
        else:
            self.auto_refresh.setText("Auto Refresh: Off")
            self.refresh_timer.stop()

    def refresh_logs(self):
        try:
            self.error_table.setRowCount(0)
            with open('destiny_hub.log', 'r') as f:
                for line in f:
                    try:
                        # Parser la ligne de log
                        parts = line.split(' - ', 2)
                        if len(parts) == 3:
                            timestamp, level, message = parts
                            
                            # Extraire la source si disponible
                            source = "System"
                            if ': ' in message:
                                source, message = message.split(': ', 1)

                            # Ajouter une nouvelle ligne
                            row = self.error_table.rowCount()
                            self.error_table.insertRow(row)
                            
                            # Remplir les colonnes
                            self.error_table.setItem(row, 0, QTableWidgetItem(timestamp))
                            self.error_table.setItem(row, 1, QTableWidgetItem(level))
                            self.error_table.setItem(row, 2, QTableWidgetItem(source))
                            self.error_table.setItem(row, 3, QTableWidgetItem(message.strip()))

                    except Exception as e:
                        logging.error(f"Failed to parse log line: {str(e)}")

            # Ajuster les colonnes
            for i in range(3):
                self.error_table.resizeColumnToContents(i)
                
        except Exception as e:
            logging.error(f"Failed to refresh logs: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to refresh logs: {str(e)}")

    def show_error_details(self):
        selected_items = self.error_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            timestamp = self.error_table.item(row, 0).text()
            level = self.error_table.item(row, 1).text()
            source = self.error_table.item(row, 2).text()
            message = self.error_table.item(row, 3).text()
            
            details = f"Timestamp: {timestamp}\n"
            details += f"Level: {level}\n"
            details += f"Source: {source}\n"
            details += f"Message: {message}\n"
            
            self.error_details.setPlainText(details)

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Gère la redirection OAuth."""
        try:
            # Extraire le code d'autorisation de l'URL
            query_components = parse_qs(urlparse(self.path).query)
            
            # Envoyer une réponse HTML
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            if 'code' in query_components:
                auth_code = query_components['code'][0]
                # Stocker le code pour l'application principale
                self.server.oauth_code = auth_code
                
                response_html = """
                <html>
                <body>
                    <h1>Authentification réussie!</h1>
                    <p>Vous pouvez fermer cette fenêtre et retourner à l'application.</p>
                    <script>window.close();</script>
                </body>
                </html>
                """
            else:
                response_html = """
                <html>
                <body>
                    <h1>Erreur d'authentification</h1>
                    <p>Code d'autorisation non trouvé.</p>
                </body>
                </html>
                """
            
            self.wfile.write(response_html.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        """Désactive les logs HTTP."""
        pass

class DestinyHub(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Destiny 2 Hub")
        self.setMinimumSize(1000, 600)
        
        # Initialiser le logger en premier
        self.setup_logging()
        self.logger = logging.getLogger('DestinyHub')
        
        # Initialiser les configurations OAuth et API
        self.OAUTH_CONFIG = {
            'client_id': '49198',  # Votre client_id de Bungie
            'api_key': os.getenv('BUNGIE_API_KEY'),  # Charger depuis .env
            'auth_url': 'https://www.bungie.net/en/OAuth/Authorize',
            'token_url': 'https://www.bungie.net/Platform/App/OAuth/token/',
            'redirect_uri': 'https://ory.ovh/'
        }
        
        # Initialisation des données utilisateur
        self.access_token = None
        self.refresh_token = None
        self.user_profile = None
        
        # Charger la session précédente
        self.load_saved_session()
        
        # Créer le widget principal et le layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # Créer et configurer le panneau de navigation
        self.setup_navigation_panel(main_layout)
        
        # Créer et configurer la zone de contenu principale
        self.setup_main_content(main_layout)
        
        # Configurer les styles
        self.setup_styles()

        self.DESTINY_COMPONENTS = {
            'profiles': '100',
            'characters': '200',
            'characterEquipment': '205',
            'characterInventories': '201',
            'characterProgressions': '202',
            'characterActivities': '204',
            'itemInstances': '300',
            'currentActivities': '204'
        }
        
        # Ajouter un cache pour les définitions d'items
        self.item_definitions_cache = {}
        self.equipment_cache = {}
        
        # Créer un thread pour le préchargement
        self.preload_thread = None

        self.setup_ui()
        self.load_saved_account()

    def setup_styles(self):
        # Set dark theme palette with Destiny 2 colors
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(18, 20, 23))  # Fond plus sombre
        palette.setColor(QPalette.ColorRole.WindowText, QColor(236, 236, 236))  # Texte plus clair
        palette.setColor(QPalette.ColorRole.Base, QColor(28, 30, 34))  # Fond des widgets
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(35, 37, 41))
        palette.setColor(QPalette.ColorRole.Text, QColor(236, 236, 236))
        palette.setColor(QPalette.ColorRole.Button, QColor(35, 37, 41))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(236, 236, 236))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(77, 122, 255))  # Bleu Destiny
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        QApplication.instance().setPalette(palette)
        
        # Style global
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #121417, stop:1 #1d1f23);
            }
            
            QPushButton {
                background-color: #4d7aff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 14px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #5d8aff;
            }
            
            QPushButton:pressed {
                background-color: #3d6aff;
            }
            
            QLineEdit {
                background-color: #2a2c30;
                border: 1px solid #3d3f43;
                border-radius: 4px;
                padding: 8px;
                color: white;
            }
            
            QLabel {
                color: #eceeee;
            }
            
            QGroupBox {
                border: 2px solid #3d3f43;
                border-radius: 6px;
                margin-top: 1em;
                padding: 15px;
                background-color: rgba(35, 37, 41, 0.7);
            }
            
            QGroupBox::title {
                color: #4d7aff;
                font-weight: bold;
                font-size: 14px;
            }
        """)

    def setup_navigation_panel(self, main_layout):
        nav_panel = QWidget()
        nav_panel.setFixedWidth(200)
        nav_layout = QVBoxLayout(nav_panel)
        
        # Title
        title_label = QLabel("Destiny 2 Hub")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(title_label)
        
        # Navigation buttons
        self.home_btn = QPushButton("Home")
        self.profile_btn = QPushButton("Profile")
        self.logs_btn = QPushButton("Error Logs")
        
        self.home_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.profile_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.logs_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        
        nav_layout.addWidget(self.home_btn)
        nav_layout.addWidget(self.profile_btn)
        nav_layout.addWidget(self.logs_btn)
        nav_layout.addStretch()
        
        main_layout.addWidget(nav_panel)

    def setup_main_content(self, main_layout):
        self.stacked_widget = QStackedWidget()
        
        # Create pages
        self.home_page = self.create_home_page()
        self.profile_page = self.create_profile_page()
        self.error_log_page = ErrorLogWidget()
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.profile_page)
        self.stacked_widget.addWidget(self.error_log_page)
        
        main_layout.addWidget(self.stacked_widget)

    def create_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Ajouter un indicateur de session
        self.session_label = QLabel()
        self.update_session_status()
        layout.addWidget(self.session_label)
        
        # Titre
        welcome_label = QLabel("Destiny 2 Hub")
        welcome_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)
        
        # Instructions
        instructions = QLabel(
            "Configuration OAuth:\n\n"
            f"• Client ID: {self.OAUTH_CONFIG['client_id']}\n"
            f"• Redirect URI: {self.OAUTH_CONFIG['redirect_uri']}\n\n"
            "Pour vous connecter:\n"
            "1. Cliquez sur 'Login with Bungie'\n"
            "2. Autorisez l'application sur Bungie.net\n"
            "3. Vous serez redirigé vers https://ory.ovh/\n"
            "4. Copiez le code depuis l'URL (après 'code=')\n"
            "5. Collez le code dans la boîte de dialogue\n"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Bouton de connexion
        login_button = QPushButton("Login with Bungie")
        login_button.clicked.connect(self.initiate_oauth_login)
        layout.addWidget(login_button)
        
        # Status
        self.auth_status_label = QLabel("Non authentifié")
        self.auth_status_label.setStyleSheet("color: red")
        layout.addWidget(self.auth_status_label)
        
        layout.addStretch()
        return page

    def create_profile_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Bungie Name input
        self.bungie_name_input = QLineEdit()
        self.bungie_name_input.setPlaceholderText("Enter Bungie Name (e.g., Guardian#1234)")
        layout.addWidget(self.bungie_name_input)
        
        # Search button
        search_btn = QPushButton("Search Profile")
        search_btn.clicked.connect(self.search_profile)
        layout.addWidget(search_btn)
        
        # Profile information display
        self.profile_info = QTextEdit()
        self.profile_info.setReadOnly(True)
        layout.addWidget(self.profile_info)
        
        return page

    def validate_api_key(self, api_key: str) -> bool:
        """Valide la clé API en faisant une requête test à l'API Bungie."""
        try:
            # Endpoint de test simple (GetCommonSettings)
            test_url = "https://www.bungie.net/Platform/Settings/"
            headers = {
                'X-API-Key': api_key,
            }

            logging.info("Testing API key validity...")
            response = requests.get(test_url, headers=headers)

            if response.status_code == 200:
                logging.info("API key is valid")
                return True
            elif response.status_code == 401:
                logging.error("API key is unauthorized")
                return False
            else:
                error_data = response.json()
                logging.error(f"API key validation failed: {error_data.get('Message', 'Unknown error')}")
                return False

        except Exception as e:
            logging.error(f"Error validating API key: {str(e)}")
            return False

    def save_api_key(self):
        """Sauvegarde et valide la clé API."""
        try:
            api_key = self.api_key_input.text().strip()
            if not api_key:
                logging.warning("Attempted to save empty API Key")
                QMessageBox.warning(self, "Error", "Please enter an API Key")
                return

            # Valider le format basique de la clé
            if len(api_key) != 32:  # Les clés API Bungie font généralement 32 caractères
                logging.warning(f"Invalid API key format: incorrect length ({len(api_key)} chars)")
                QMessageBox.warning(self, "Error", "Invalid API key format. Please check your key.")
                return

            # Tester la clé API
            if not self.validate_api_key(api_key):
                QMessageBox.warning(self, "Error", 
                    "Invalid API key. Please make sure you've copied the correct key from Bungie.net")
                return

            # Si la validation réussit, sauvegarder la clé
            with open('.env', 'w') as f:
                f.write(f'BUNGIE_API_KEY={api_key}')
            self.api_key = api_key
            
            logging.info("API Key saved and validated successfully")
            QMessageBox.information(self, "Success", 
                "API Key validated and saved successfully!")

            # Ajouter un label pour montrer que la clé est valide
            self.api_status_label.setText("API Status: Connected")
            self.api_status_label.setStyleSheet("color: green")

        except Exception as e:
            logging.error(f"Failed to save API Key: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to save API Key: {str(e)}")

    def find_available_port(self, start_port=8000, max_port=8999):
        """Trouve un port disponible pour le serveur local."""
        for port in range(start_port, max_port + 1):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except socket.error:
                continue
        raise Exception("Aucun port disponible trouvé")

    def start_oauth_server(self):
        """Démarre le serveur local pour la redirection OAuth."""
        try:
            # Créer et démarrer le serveur
            self.oauth_server = HTTPServer(('localhost', self.server_port), OAuthCallbackHandler)
            self.oauth_server.oauth_code = None
            
            self.server_thread = threading.Thread(target=self.oauth_server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            logging.info(f"Serveur OAuth démarré sur le port {self.server_port}")
            
        except Exception as e:
            logging.error(f"Erreur lors du démarrage du serveur OAuth: {str(e)}")
            raise

    def stop_oauth_server(self):
        """Arrête le serveur OAuth local."""
        if self.oauth_server:
            self.oauth_server.shutdown()
            self.oauth_server.server_close()
            self.server_thread = None
            logging.info("Serveur OAuth arrêté")

    def initiate_oauth_login(self):
        """Démarre le processus d'authentification OAuth."""
        try:
            # Vérification explicite de l'URL de redirection
            if 'localhost' in self.OAUTH_CONFIG['redirect_uri']:
                raise ValueError("URL de redirection incorrecte détectée")
                
            # Log de débogage
            logging.info(f"Démarrage OAuth avec redirect_uri: {self.OAUTH_CONFIG['redirect_uri']}")
            
            params = {
                'client_id': self.OAUTH_CONFIG['client_id'],
                'response_type': 'code',
                'redirect_uri': self.OAUTH_CONFIG['redirect_uri'],
                'state': 'destiny2hub'
            }
            
            # Vérification des paramètres
            logging.debug(f"Paramètres de la requête: {params}")
            
            auth_url = f"{self.OAUTH_CONFIG['auth_url']}?{urlencode(params)}"
            logging.info(f"URL d'autorisation générée: {auth_url}")
            
            # Ouvrir le navigateur
            webbrowser.open(auth_url)
            
            # Boîte de dialogue pour le code
            code, ok = QInputDialog.getText(
                self,
                "Code d'autorisation",
                "Une fois redirigé vers https://ory.ovh/, copiez le code depuis l'URL\n"
                "(cherchez 'code=' dans l'URL) et collez-le ici:\n\n"
                "Note: Copiez uniquement le code, pas l'URL entière"
            )
            
            if ok and code:
                code = code.strip()
                if '=' in code:
                    code = code.split('code=')[-1].split('&')[0]
                logging.info(f"Code d'autorisation reçu (longueur: {len(code)})")
                self.complete_oauth(code)
            
        except Exception as e:
            logging.error(f"Erreur lors de l'initialisation OAuth: {str(e)}")
            QMessageBox.warning(self, "Erreur", f"Erreur d'authentification: {str(e)}")

    def complete_oauth(self, auth_code):
        """Complète le processus OAuth avec le code d'autorisation."""
        try:
            headers = {
                'X-API-Key': self.OAUTH_CONFIG['api_key'],
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'client_id': self.OAUTH_CONFIG['client_id'],
                'redirect_uri': self.OAUTH_CONFIG['redirect_uri']
            }
            
            logging.debug(f"Envoi de la requête token avec les données: {data}")
            
            response = requests.post(
                self.OAUTH_CONFIG['token_url'],
                headers=headers,
                data=data
            )
            
            logging.debug(f"Réponse reçue: Status {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                logging.debug(f"Token data reçue: {token_data.keys()}")
                
                # Stockage des tokens avec vérification
                self.access_token = token_data.get('access_token')
                self.refresh_token = token_data.get('refresh_token')
                
                if self.access_token:
                    # Sauvegarder les tokens disponibles
                    self.save_tokens(token_data)
                    
                    # Message de succès avec détails
                    success_msg = "Authentification réussie!\n"
                    success_msg += f"Access Token reçu: {'Oui' if self.access_token else 'Non'}\n"
                    success_msg += f"Refresh Token reçu: {'Oui' if self.refresh_token else 'Non'}"
                    
                    logging.info("Authentification OAuth réussie")
                    QMessageBox.information(self, "Succès", success_msg)
                    self.update_auth_status("Authentifié")
                else:
                    raise ValueError("Access token non reçu dans la réponse")
                
            else:
                # Afficher les détails de l'erreur
                try:
                    error_data = response.json()
                    error_msg = (f"Erreur de requête token: "
                               f"{error_data.get('error_description', response.text)}\n"
                               f"Code HTTP: {response.status_code}")
                except:
                    error_msg = f"Erreur HTTP {response.status_code}: {response.text}"
                
                logging.error(error_msg)
                QMessageBox.warning(self, "Erreur", error_msg)
                
        except Exception as e:
            error_msg = f"Erreur lors de la completion OAuth: {str(e)}"
            logging.error(error_msg)
            # Afficher plus de détails pour le débogage
            logging.error(f"Détails de l'exception: {type(e).__name__}")
            QMessageBox.warning(self, "Erreur", error_msg)

    def save_tokens(self, token_data):
        """Sauvegarde les tokens d'authentification."""
        try:
            with open('auth_tokens.json', 'w') as f:
                json.dump(token_data, f)
            logging.info("Authentication tokens saved successfully")
        except Exception as e:
            logging.error(f"Failed to save authentication tokens: {str(e)}")

    def load_tokens(self):
        """Charge les tokens sauvegardés."""
        try:
            if os.path.exists('auth_tokens.json'):
                with open('auth_tokens.json', 'r') as f:
                    token_data = json.load(f)
                self.access_token = token_data['access_token']
                self.refresh_token = token_data['refresh_token']
                logging.info("Authentication tokens loaded successfully")
                return True
        except Exception as e:
            logging.error(f"Failed to load authentication tokens: {str(e)}")
        return False

    def update_auth_status(self, status):
        """Met à jour l'affichage du statut d'authentification."""
        self.auth_status_label.setText(f"Auth Status: {status}")
        if status == "Authenticated":
            self.auth_status_label.setStyleSheet("color: green")
        else:
            self.auth_status_label.setStyleSheet("color: red")

    def load_saved_session(self):
        """Charge la session sauvegardée et les données utilisateur."""
        try:
            # Charger les tokens
            if os.path.exists('auth_tokens.json'):
                with open('auth_tokens.json', 'r') as f:
                    token_data = json.load(f)
                    self.access_token = token_data.get('access_token')
                    self.refresh_token = token_data.get('refresh_token')
                    logging.info("Tokens chargés depuis le fichier")
                    
                    # Rafraîchir le token si nécessaire
                    if self.access_token:
                        self.validate_and_refresh_token()
            
            # Charger le profil utilisateur
            if os.path.exists('user_profile.json'):
                with open('user_profile.json', 'r') as f:
                    self.user_profile = json.load(f)
                    logging.info("Profil utilisateur chargé")
                    
        except Exception as e:
            logging.error(f"Erreur lors du chargement de la session: {str(e)}")

    def validate_and_refresh_token(self):
        """Valide le token actuel et le rafraîchit si nécessaire."""
        try:
            # Tester le token actuel
            headers = {
                'X-API-Key': self.OAUTH_CONFIG['api_key'],
                'Authorization': f'Bearer {self.access_token}'
            }
            
            # Faire une requête test à l'API
            test_response = requests.get(
                'https://www.bungie.net/Platform/User/GetCurrentBungieNetUser/',
                headers=headers
            )
            
            if test_response.status_code != 200:
                # Token expiré, essayer de le rafraîchir
                if self.refresh_token:
                    self.refresh_access_token()
                else:
                    logging.warning("Pas de refresh token disponible")
                    self.access_token = None
                    
        except Exception as e:
            logging.error(f"Erreur lors de la validation du token: {str(e)}")

    def refresh_access_token(self):
        """Rafraîchit le token d'accès avec le refresh token."""
        try:
            headers = {
                'X-API-Key': self.OAUTH_CONFIG['api_key'],
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.OAUTH_CONFIG['client_id']
            }
            
            response = requests.post(
                self.OAUTH_CONFIG['token_url'],
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                self.refresh_token = token_data.get('refresh_token')
                self.save_tokens(token_data)
                logging.info("Token rafraîchi avec succès")
            else:
                logging.error("Échec du rafraîchissement du token")
                self.access_token = None
                self.refresh_token = None
                
        except Exception as e:
            logging.error(f"Erreur lors du rafraîchissement du token: {str(e)}")

    def save_user_profile(self, profile_data):
        """Sauvegarde les informations du profil utilisateur."""
        try:
            with open('user_profile.json', 'w') as f:
                json.dump(profile_data, f, indent=4)
            self.user_profile = profile_data
            logging.info("Profil utilisateur sauvegardé")
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde du profil: {str(e)}")

    def load_user_profile(self):
        """Charge et affiche le profil utilisateur sauvegardé."""
        if self.user_profile:
            self.display_profile_info(self.user_profile)
            return True
        return False

    def search_profile(self):
        """Recherche le profil utilisateur ou utilise le profil sauvegardé."""
        if not self.access_token:
            if not self.load_saved_session():
                logging.warning("Authentification requise")
                QMessageBox.warning(self, "Erreur", "Veuillez vous authentifier d'abord")
                return

        # Si nous avons déjà un profil sauvegardé, l'utiliser
        if self.load_user_profile():
            return

        # Sinon, faire la recherche normale
        try:
            bungie_name = self.bungie_name_input.text()
            if not bungie_name or '#' not in bungie_name:
                logging.warning("Format de Bungie Name invalide")
                QMessageBox.warning(self, "Erreur", "Format de Bungie Name invalide (ex: Guardian#1234)")
                return

            display_name, display_name_code = bungie_name.split('#')
            
            # Log the search attempt
            logging.info(f"Searching for player: {display_name}#{display_name_code}")
            
            headers = {
                'X-API-Key': self.OAUTH_CONFIG['api_key'],
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'displayName': display_name,
                'displayNameCode': int(display_name_code)
            }
            
            # Log the request details (excluding sensitive info)
            logging.debug(f"Making request to Bungie API for player search - DisplayName: {display_name}")
            
            response = requests.post(
                'https://www.bungie.net/Platform/Destiny2/SearchDestinyPlayerByBungieName/3/',
                headers=headers,
                json=data
            )
            
            # Log the response status
            logging.debug(f"Bungie API response status: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"API request failed with status code: {response.status_code}"
                logging.error(error_msg)
                try:
                    error_details = response.json()
                    logging.error(f"API Error details: {json.dumps(error_details, indent=2)}")
                    if 'Message' in error_details:
                        error_msg += f"\nAPI Message: {error_details['Message']}"
                except:
                    logging.error("Could not parse error response from API")
                QMessageBox.warning(self, "Error", error_msg)
                return

            response_data = response.json()
            
            # Vérifier la structure de la réponse
            if 'Response' not in response_data:
                error_msg = "Invalid API response structure"
                logging.error(f"{error_msg}: {json.dumps(response_data, indent=2)}")
                QMessageBox.warning(self, "Error", error_msg)
                return

            if not response_data['Response']:
                error_msg = f"Player not found: {bungie_name}"
                logging.warning(error_msg)
                QMessageBox.warning(self, "Error", error_msg)
                return

            player_info = response_data['Response'][0]
            membership_id = player_info['membershipId']
            
            logging.info(f"Found player. MembershipId: {membership_id}")
            
            # Get detailed profile information
            profile_url = f'https://www.bungie.net/Platform/Destiny2/3/Profile/{membership_id}/'
            if response.status_code == 200:
                result = response.json()
                if result['Response']:
                    player_info = result['Response'][0]
                    membership_id = player_info['membershipId']
                    
                    # Get detailed profile information
                    profile_response = requests.get(
                        f'https://www.bungie.net/Platform/Destiny2/3/Profile/{membership_id}/',
                        headers=headers,
                        params={'components': '100,200'}  # Profile and Characters components
                    )
                    
                    if profile_response.status_code == 200:
                        profile_data = profile_response.json()['Response']
                        self.save_user_profile(profile_data)
                        self.display_profile_info(profile_data)
                    else:
                        QMessageBox.warning(self, "Error", "Failed to fetch profile details")
                else:
                    QMessageBox.warning(self, "Error", "Player not found")
            else:
                QMessageBox.warning(self, "Error", "Failed to search for player")
                
        except Exception as e:
            logging.error(f"Erreur lors de la recherche du profil: {str(e)}")
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la recherche: {str(e)}")

    def display_profile_info(self, profile_data):
        self.profile_info.clear()
        
        profile = profile_data.get('profile', {}).get('data', {})
        characters = profile_data.get('characters', {}).get('data', {})
        
        info_text = "Profile Information:\n\n"
        
        if profile:
            info_text += f"Last Played: {profile.get('dateLastPlayed', 'Unknown')}\n"
            info_text += f"Minutes Played: {profile.get('minutesPlayedTotal', 0)}\n"
            info_text += f"Character Count: {len(characters)}\n\n"
        
        if characters:
            info_text += "Characters:\n"
            for char_id, char_data in characters.items():
                info_text += f"\nClass: {char_data.get('classType', 'Unknown')}\n"
                info_text += f"Light Level: {char_data.get('light', 0)}\n"
                info_text += f"Race: {char_data.get('raceType', 'Unknown')}\n"
                info_text += "-" * 30 + "\n"
        
        self.profile_info.setText(info_text)

    def update_session_status(self):
        """Met à jour l'affichage du statut de la session avec un style amélioré."""
        status_style = """
            QLabel {
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
        """
        
        if self.access_token and self.user_profile:
            self.session_label.setText("● Session active - Profil chargé")
            self.session_label.setStyleSheet(
                status_style + "background-color: rgba(46, 204, 113, 0.2); color: #2ecc71;"
            )
        elif self.access_token:
            self.session_label.setText("● Session active - Profil non chargé")
            self.session_label.setStyleSheet(
                status_style + "background-color: rgba(241, 196, 15, 0.2); color: #f1c40f;"
            )
        else:
            self.session_label.setText("● Aucune session active")
            self.session_label.setStyleSheet(
                status_style + "background-color: rgba(231, 76, 60, 0.2); color: #e74c3c;"
            )

    def handle_log(self, message):
        """Gestion sûre des logs dans l'interface."""
        try:
            if hasattr(self, 'error_log_page') and not self.error_log_page.isHidden():
                self.error_log_page.log_text.append(message)
        except Exception:
            pass  # Ignorer silencieusement les erreurs d'interface

    def setup_logging(self):
        """Configure le système de logging de manière détaillée."""
        try:
            # Configuration du fichier de log
            logging.basicConfig(
                filename='destiny_hub.log',
                level=logging.DEBUG,  # Changé à DEBUG pour plus de détails
                format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Ajouter aussi les logs dans la console
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            logging.getLogger('').addHandler(console_handler)
            
            # Log de démarrage
            logging.info("=== Démarrage de Destiny Hub ===")
            logging.info(f"Version Python: {sys.version}")
            logging.info(f"Système d'exploitation: {sys.platform}")
            
            # Vérification des dépendances
            logging.info("Vérification des dépendances:")
            try:
                import PyQt6
                logging.info(f"PyQt6 version: {PyQt6.__version__}")
            except:
                logging.warning("PyQt6 non trouvé")
            
            try:
                import requests
                logging.info(f"Requests version: {requests.__version__}")
            except:
                logging.warning("Requests non trouvé")
            
            try:
                import dotenv
                logging.info(f"python-dotenv version: {dotenv.__version__}")
            except:
                logging.warning("python-dotenv non trouvé")
            
            try:
                import psutil
                logging.info(f"psutil version: {psutil.__version__}")
            except:
                logging.warning("psutil non trouvé")
            
            # Vérification des dossiers nécessaires
            logging.info("Vérification des dossiers:")
            if not os.path.exists('data'):
                os.makedirs('data')
                logging.info("Dossier 'data' créé")
            else:
                logging.info("Dossier 'data' existant")
            
            if not os.path.exists('icons'):
                os.makedirs('icons')
                logging.info("Dossier 'icons' créé")
            else:
                logging.info("Dossier 'icons' existant")
            
            # Vérification du fichier .env
            if os.path.exists('.env'):
                logging.info("Fichier .env trouvé")
                if os.getenv('BUNGIE_API_KEY'):
                    logging.info("Clé API Bungie trouvée dans .env")
                else:
                    logging.warning("Clé API Bungie non trouvée dans .env")
            else:
                logging.warning("Fichier .env non trouvé")
            
        except Exception as e:
            logging.error(f"Erreur lors de la configuration du logging: {str(e)}")

    def setup_ui(self):
        """Configuration de l'interface utilisateur."""
        # Widget central et layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header avec les onglets et icônes
        header = QWidget()
        header.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-bottom: 1px solid #333;
            }
            QPushButton {
                border: none;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #333;
            }
            QPushButton:checked {
                background-color: #444;
                border-bottom: 2px solid #2a82da;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 0, 10, 0)

        # Boutons du header avec icônes
        self.account_btn = QPushButton("Compte")
        self.account_btn.setCheckable(True)
        self.account_btn.setIcon(QIcon("icons/user.png"))  # Ajouter l'icône d'utilisateur
        
        self.equipment_btn = QPushButton("Équipement")
        self.equipment_btn.setCheckable(True)
        self.equipment_btn.setIcon(QIcon("icons/bag.png"))  # Ajouter l'icône de sac
        
        self.missions_btn = QPushButton("Missions")
        self.missions_btn.setCheckable(True)
        self.missions_btn.setIcon(QIcon("icons/tasks.png"))  # Ajouter l'icône de cahier

        header_layout.addWidget(self.account_btn)
        header_layout.addWidget(self.equipment_btn)
        header_layout.addWidget(self.missions_btn)
        header_layout.addStretch()

        main_layout.addWidget(header)

        # Stacked widget pour les différentes pages
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Créer les pages
        self.account_page = self.create_account_page()
        self.equipment_page = self.create_equipment_page()
        self.missions_page = self.create_missions_page()

        self.stacked_widget.addWidget(self.account_page)
        self.stacked_widget.addWidget(self.equipment_page)
        self.stacked_widget.addWidget(self.missions_page)

        # Connecter les boutons
        self.account_btn.clicked.connect(lambda: self.switch_page(0))
        self.equipment_btn.clicked.connect(lambda: self.switch_page(1))
        self.missions_btn.clicked.connect(lambda: self.switch_page(2))

    def create_account_page(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Groupe Compte
        account_group = QGroupBox("Compte Destiny 2")
        account_layout = QVBoxLayout()
        
        # Statut du compte
        self.account_status = QLabel("Aucun compte enregistré")
        account_layout.addWidget(self.account_status)
        
        # Input Bungie Name
        self.bungie_name_input = QLineEdit()
        self.bungie_name_input.setPlaceholderText("Entrez votre Bungie Name (ex: per#8639)")
        account_layout.addWidget(self.bungie_name_input)
        
        # Bouton d'enregistrement
        save_button = QPushButton("Enregistrer le compte")
        save_button.clicked.connect(self.register_account)
        account_layout.addWidget(save_button)
        
        account_group.setLayout(account_layout)
        layout.addWidget(account_group)
        
        # Informations du compte
        self.account_info = QTextEdit()
        self.account_info.setReadOnly(True)
        layout.addWidget(self.account_info)
        
        return tab

    def create_equipment_page(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Style amélioré pour la page d'équipement
        equipment_style = """
            QWidget#equipment_slot {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 rgba(45, 47, 51, 0.9),
                                          stop:1 rgba(35, 37, 41, 0.9));
                border: 2px solid #3d3f43;
                border-radius: 8px;
                padding: 10px;
            }
            
            QWidget#equipment_slot:hover {
                border-color: #4d7aff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 rgba(55, 57, 61, 0.9),
                                          stop:1 rgba(45, 47, 51, 0.9));
            }
            
            QLabel#power {
                color: #ffd700;
                font-size: 18px;
                font-weight: bold;
                font-family: 'Arial';
            }
            
            QLabel#item_name {
                color: #eceeee;
                font-size: 13px;
                font-weight: bold;
                margin-top: 5px;
            }
            
            QLabel#icon_label {
                background-color: transparent;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                padding: 2px;
            }
        """
        page.setStyleSheet(equipment_style)

        # Colonne gauche (armes)
        weapons_column = QVBoxLayout()
        weapons_column.setSpacing(10)
        weapons_column.setContentsMargins(20, 20, 20, 20)
        
        # Créer les slots d'armes
        self.weapon_slots = []
        for weapon_type in ['kinetic', 'energy', 'power']:
            slot = QWidget()
            slot.setObjectName("equipment_slot")
            slot_layout = QVBoxLayout(slot)
            slot_layout.setContentsMargins(5, 5, 5, 5)
            
            # Ajouter les labels nécessaires pour chaque slot
            icon_label = QLabel()
            icon_label.setFixedSize(64, 64)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setObjectName("icon_label")  # Ajouter un nom d'objet
            icon_label.setScaledContents(True)  # Permettre le redimensionnement du contenu
            
            power_label = QLabel("0")
            power_label.setObjectName("power")
            power_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            name_label = QLabel("Vide")
            name_label.setObjectName("item_name")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setWordWrap(True)
            
            slot_layout.addWidget(icon_label)
            slot_layout.addWidget(power_label)
            slot_layout.addWidget(name_label)
            
            weapons_column.addWidget(slot)
            self.weapon_slots.append(slot)
        
        weapons_column.addStretch()

        # Zone centrale (personnage)
        character_widget = QWidget()
        character_layout = QVBoxLayout(character_widget)
        
        # Niveau de puissance
        power_label = QLabel("POWER")
        power_label.setStyleSheet("color: white; font-size: 20px;")
        power_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        character_layout.addWidget(power_label)
        
        self.power_value = QLabel("1801")
        self.power_value.setStyleSheet("color: #FFEB3B; font-size: 32px; font-weight: bold;")
        self.power_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        character_layout.addWidget(self.power_value)
        
        # Placeholder pour le personnage
        character_view = QLabel()
        character_view.setFixedSize(400, 600)
        character_view.setStyleSheet("background-color: rgba(0, 0, 0, 0.3); border-radius: 10px;")
        character_layout.addWidget(character_view)

        # Colonne droite (armure)
        armor_column = QVBoxLayout()
        armor_column.setSpacing(10)
        armor_column.setContentsMargins(20, 20, 20, 20)
        
        # Créer les slots d'armure
        self.armor_slots = []
        for armor_type in ['helmet', 'gauntlets', 'chest', 'legs', 'class_item']:
            slot = QWidget()
            slot.setObjectName("equipment_slot")
            slot_layout = QVBoxLayout(slot)
            slot_layout.setContentsMargins(5, 5, 5, 5)
            
            # Ajouter les labels nécessaires pour chaque slot
            icon_label = QLabel()
            icon_label.setFixedSize(64, 64)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setObjectName("icon_label")  # Ajouter un nom d'objet
            icon_label.setScaledContents(True)  # Permettre le redimensionnement du contenu
            
            power_label = QLabel("0")
            power_label.setObjectName("power")
            power_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            name_label = QLabel("Vide")
            name_label.setObjectName("item_name")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setWordWrap(True)
            
            slot_layout.addWidget(icon_label)
            slot_layout.addWidget(power_label)
            slot_layout.addWidget(name_label)
            
            armor_column.addWidget(slot)
            self.armor_slots.append(slot)
        
        armor_column.addStretch()

        # Ajouter les colonnes au layout principal
        layout.addLayout(weapons_column)
        layout.addWidget(character_widget)
        layout.addLayout(armor_column)

        # Charger l'équipement du personnage actif
        self.load_active_character()

        return page

    def display_equipment(self, equipment):
        try:
            self.logger.info("=== Début de l'affichage des équipements ===")
            
            # Trier l'équipement par type
            sorted_equipment = {
                'weapons': [],
                'armor': []
            }

            # Calculer la puissance totale (uniquement pour les items d'équipement valides)
            total_power = 0
            valid_items = 0

            for item in equipment:
                power = item.get('instance', {}).get('primaryStat', {}).get('value', 0)
                bucket_hash = str(item.get('bucketHash', ''))
                bucket_type = self.get_bucket_type(bucket_hash)
                
                self.logger.info(f"🔍 Analyse item - BucketHash: {bucket_hash}, Type: {bucket_type}")
                self.logger.info(f"   Puissance: {power}")

                # Ne compter que les items d'équipement valides (armes et armure)
                if bucket_type in ['kinetic', 'energy', 'power', 'helmet', 'gauntlets', 'chest', 'legs', 'class_item']:
                    if power > 1000:  # Vérifier que c'est un item valide avec une puissance normale
                        total_power += power
                        valid_items += 1
                        self.logger.info(f"   ✅ Item valide compté pour la puissance moyenne")
                    else:
                        self.logger.info(f"   ⚠️ Item ignoré car puissance trop basse: {power}")

                if bucket_type in ['kinetic', 'energy', 'power']:
                    sorted_equipment['weapons'].append(item)
                elif bucket_type in ['helmet', 'gauntlets', 'chest', 'legs', 'class_item']:
                    sorted_equipment['armor'].append(item)

            # Mise à jour de la puissance moyenne
            if valid_items > 0:
                average_power = total_power // valid_items
                self.logger.info(f"💪 Puissance moyenne calculée: {average_power} (Total: {total_power} / Items: {valid_items})")
                self.power_value.setText(str(average_power))
            else:
                self.logger.warning("⚠️ Aucun item valide pour calculer la puissance")
                self.power_value.setText("0")

            # Mise à jour des slots
            self.logger.info(f"🗡️ Armes trouvées: {len(sorted_equipment['weapons'])}")
            self.logger.info(f"🛡️ Pièces d'armure trouvées: {len(sorted_equipment['armor'])}")

            # Mise à jour des slots d'armes
            for i, slot in enumerate(self.weapon_slots):
                if i < len(sorted_equipment['weapons']):
                    self.logger.info(f"📦 Mise à jour du slot d'arme {i+1}")
                    self.update_equipment_slot(slot, sorted_equipment['weapons'][i])

            # Mise à jour des slots d'armure
            for i, slot in enumerate(self.armor_slots):
                if i < len(sorted_equipment['armor']):
                    self.logger.info(f"📦 Mise à jour du slot d'armure {i+1}")
                    self.update_equipment_slot(slot, sorted_equipment['armor'][i])

            self.logger.info("✅ Affichage des équipements terminé")

        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'affichage des équipements: {str(e)}")
            self.logger.exception("   Détails de l'erreur:")

    def update_equipment_slot(self, slot, item):
        try:
            self.logger.info(f"=== Mise à jour du slot d'équipement ===")
            
            layout = slot.layout()
            if not layout:
                self.logger.error("❌ Layout non trouvé pour le slot")
                return

            # Récupérer le hash de l'item
            item_hash = str(item.get('itemHash', ''))
            self.logger.info(f"🔍 Récupération des définitions pour l'item {item_hash}")

            # Faire la requête à l'API Manifest
            headers = {
                'X-API-Key': self.OAUTH_CONFIG['api_key'],
                'Content-Type': 'application/json'
            }
            manifest_url = f"https://www.bungie.net/Platform/Destiny2/Manifest/DestinyInventoryItemDefinition/{item_hash}/"
            
            response = requests.get(manifest_url, headers=headers)
            if response.status_code == 200:
                item_def = response.json()['Response']
                item_name = item_def['displayProperties']['name']
                icon_path = item_def['displayProperties']['icon']
                icon_url = f"https://www.bungie.net{icon_path}"
                
                self.logger.info(f"✅ Item trouvé: {item_name}")
                self.logger.info(f"🖼️ Icône: {icon_url}")

                # Mise à jour de l'icône
                icon_label = layout.itemAt(0).widget()
                icon_filename = f"icons/{item_hash}.png"
                
                if not self.verify_image_file(icon_filename):
                    self.logger.error(f"❌ Image invalide: {icon_filename}")
                    # Retélécharger l'image
                    icon_response = requests.get(icon_url)
                    if icon_response.status_code == 200:
                        with open(icon_filename, 'wb') as f:
                            f.write(icon_response.content)

                pixmap = QPixmap(icon_filename)
                if pixmap.isNull():
                    self.logger.error(f"❌ Échec du chargement du pixmap pour {icon_filename}")
                    # Vérifier le format du fichier
                    with open(icon_filename, 'rb') as f:
                        header = f.read(8)
                        self.logger.info(f"En-tête du fichier: {header.hex()}")
                    return
                
                self.logger.info(f"📏 Dimensions originales: {pixmap.width()}x{pixmap.height()}")
                
                # Redimensionner
                scaled_pixmap = pixmap.scaled(
                    64, 64,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                if scaled_pixmap.isNull():
                    self.logger.error("❌ Échec du redimensionnement")
                    return
                
                self.logger.info(f"📏 Dimensions après redimensionnement: {scaled_pixmap.width()}x{scaled_pixmap.height()}")
                
                # Appliquer au label
                icon_label.setPixmap(scaled_pixmap)
                self.logger.info("✅ Image appliquée au label")

                # Mise à jour de la puissance
                power = item.get('instance', {}).get('primaryStat', {}).get('value', 0)
                power_label = layout.itemAt(1).widget()
                power_label.setText(str(power))

                # Mise à jour du nom
                name_label = layout.itemAt(2).widget()
                name_label.setText(item_name)
                
            else:
                self.logger.error(f"❌ Erreur lors de la récupération des définitions: {response.status_code}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la mise à jour de l'affichage: {str(e)}")
            self.logger.exception("   Détails de l'erreur:")

    def get_bucket_type(self, bucket_hash):
        """Retourne le type d'emplacement d'équipement basé sur le bucket hash."""
        # Mapping des bucket hash vers les types d'équipement
        bucket_types = {
            '1498876634': 'kinetic',    # Arme cinétique
            '2465295065': 'energy',     # Arme énergétique
            '953998645': 'power',       # Arme lourde
            '3448274439': 'helmet',     # Casque
            '3551918588': 'gauntlets',  # Gants
            '14239492': 'chest',        # Torse
            '20886954': 'legs',         # Jambes
            '1585787867': 'class_item', # Objet de classe
            '4023194814': 'ghost',      # Spectre
        }
        return bucket_types.get(bucket_hash, 'unknown')

    def register_account(self):
        """Enregistre un nouveau compte Destiny 2."""
        try:
            bungie_name = self.bungie_name_input.text().strip()
            self.logger.info(f"Tentative d'enregistrement du compte: {bungie_name}")
            
            # Vérifier le format du Bungie Name
            if not bungie_name or '#' not in bungie_name:
                self.logger.warning(f"Format de Bungie Name invalide: {bungie_name}")
                QMessageBox.warning(self, "Erreur", "Format de Bungie Name invalide (ex: Guardian#1234)")
                return

            display_name, display_name_code = bungie_name.split('#')
            
            # Vérifier la clé API
            if not self.OAUTH_CONFIG['api_key']:
                self.logger.error("Clé API manquante dans la configuration")
                QMessageBox.warning(self, "Erreur", "Clé API Bungie non configurée")
                return
            
            # Préparer les headers avec uniquement la clé API (pas besoin de token ici)
            headers = {
                'X-API-Key': self.OAUTH_CONFIG['api_key']
            }
            
            # Préparer les données de recherche
            search_data = {
                'displayName': display_name,
                'displayNameCode': int(display_name_code)
            }
            
            # Faire la requête
            response = requests.post(
                'https://www.bungie.net/Platform/Destiny2/SearchDestinyPlayerByBungieName/-1/',  # -1 pour chercher sur toutes les plateformes
                headers=headers,
                json=search_data
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
                    
                    QMessageBox.information(self, "Succès", "Compte enregistré avec succès!")
                else:
                    self.logger.warning("Compte non trouvé")
                    QMessageBox.warning(self, "Erreur", "Compte Destiny 2 non trouvé")
            else:
                error_msg = f"Erreur API: {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        error_msg += f"\n{error_data.get('Message', '')}"
                    except:
                        error_msg += f"\n{response.text}"
                
                self.logger.error(error_msg)
                QMessageBox.warning(self, "Erreur", error_msg)
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement du compte: {str(e)}")
            self.logger.exception("Détails de l'erreur:")

    def get_auth_headers(self):
        """Retourne les headers nécessaires pour les requêtes à l'API Bungie."""
        headers = {
            'X-API-Key': self.OAUTH_CONFIG['api_key'],
            'Content-Type': 'application/json'
        }
        
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        return headers

    def create_missions_page(self):
        """Crée la page des missions."""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # En-tête avec le statut du jeu
        status_layout = QHBoxLayout()
        self.game_status_label = QLabel("Statut de Destiny 2: Non détecté")
        self.game_status_label.setStyleSheet("color: red;")
        status_layout.addWidget(self.game_status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # Zone de scroll pour les missions
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Widget contenant les missions
        missions_widget = QWidget()
        self.missions_layout = QVBoxLayout(missions_widget)
        
        # Style pour les missions
        missions_widget.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
            }
            QLabel {
                color: white;
            }
            QGroupBox {
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 1ex;
                padding: 10px;
                background-color: rgba(0, 0, 0, 0.3);
            }
            QGroupBox::title {
                color: #2a82da;
            }
        """)
        
        # Message par défaut
        self.no_missions_label = QLabel("Aucune mission active\nLancez Destiny 2 pour voir vos missions")
        self.no_missions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.missions_layout.addWidget(self.no_missions_label)
        
        scroll_area.setWidget(missions_widget)
        layout.addWidget(scroll_area)
        
        # Timer pour vérifier le statut du jeu
        self.game_check_timer = QTimer()
        self.game_check_timer.timeout.connect(self.check_game_status)
        self.game_check_timer.start(5000)  # Vérifier toutes les 5 secondes
        
        return page

    def check_game_status(self):
        """Vérifie si Destiny 2 est en cours d'exécution."""
        try:
            destiny2_running = False
            logging.debug("Vérification du statut de Destiny 2...")
            
            for process in psutil.process_iter(['name', 'pid']):
                if process.info['name'] == 'destiny2.exe':
                    destiny2_running = True
                    logging.info(f"Destiny 2 trouvé - PID: {process.info['pid']}")
                    break
            
            if destiny2_running:
                logging.info("Destiny 2 est en cours d'exécution")
                self.game_status_label.setText("Statut de Destiny 2: En cours d'exécution")
                self.game_status_label.setStyleSheet("color: green;")
                self.update_missions()
            else:
                logging.debug("Destiny 2 n'est pas en cours d'exécution")
                self.game_status_label.setText("Statut de Destiny 2: Non détecté")
                self.game_status_label.setStyleSheet("color: red;")
                self.no_missions_label.show()
                
        except Exception as e:
            logging.error(f"Erreur lors de la vérification du statut du jeu: {str(e)}")
            logging.exception("Détails de l'erreur:")

    def update_missions(self):
        """Met à jour la liste des missions actives."""
        try:
            # Cacher le message "pas de mission"
            self.no_missions_label.hide()
            
            # Nettoyer les anciennes missions
            while self.missions_layout.count() > 1:  # Garder le label "pas de mission"
                item = self.missions_layout.takeAt(1)
                if item.widget():
                    item.widget().deleteLater()
            
            # Pour test, ajouter quelques missions fictives
            test_missions = [
                {
                    'name': 'Mission hebdomadaire',
                    'description': 'Complétez 3 activités de n\'importe quel type',
                    'progress': '1/3'
                },
                {
                    'name': 'Défi du Gardien',
                    'description': 'Éliminez 50 ennemis avec des armes énergétiques',
                    'progress': '23/50'
                }
            ]
            
            # Créer un groupe pour chaque mission
            for mission in test_missions:
                mission_group = QGroupBox(mission['name'])
                mission_layout = QVBoxLayout()
                
                description = QLabel(mission['description'])
                description.setWordWrap(True)
                mission_layout.addWidget(description)
                
                progress = QLabel(f"Progression: {mission['progress']}")
                progress.setStyleSheet("color: #2a82da;")
                mission_layout.addWidget(progress)
                
                mission_group.setLayout(mission_layout)
                self.missions_layout.addWidget(mission_group)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour des missions: {str(e)}")

    def load_saved_account(self):
        """Charge les informations du compte sauvegardé."""
        try:
            # Vérifier si le dossier data existe
            if not os.path.exists('data'):
                os.makedirs('data')
                self.logger.info("Dossier 'data' créé")
                return

            # Charger les informations du compte
            if os.path.exists('data/account.json'):
                with open('data/account.json', 'r') as f:
                    account_data = json.load(f)
                    
                # Mettre à jour l'interface
                self.bungie_name_input.setText(account_data.get('bungie_name', ''))
                self.account_status.setText(f"Compte enregistré: {account_data.get('bungie_name', '')}")
                self.account_status.setStyleSheet("color: green;")
                
                # Charger les données complètes si disponibles
                if os.path.exists('data/full_account.json'):
                    with open('data/full_account.json', 'r') as f:
                        full_data = json.load(f)
                    self.display_profile_info(full_data)
                    
                self.logger.info("Compte chargé avec succès")
            else:
                self.logger.info("Aucun compte sauvegardé trouvé")
                
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du compte: {str(e)}")
            QMessageBox.warning(self, "Erreur", f"Impossible de charger le compte: {str(e)}")

    def switch_page(self, index):
        """Change la page active et met à jour les boutons de navigation."""
        try:
            # Changer la page
            self.stacked_widget.setCurrentIndex(index)
            
            # Mettre à jour l'état des boutons
            self.account_btn.setChecked(index == 0)
            self.equipment_btn.setChecked(index == 1)
            self.missions_btn.setChecked(index == 2)
            
            self.logger.info(f"Page changée vers l'index {index}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du changement de page: {str(e)}")

    def load_active_character(self):
        try:
            self.logger.info("=== Début du chargement du personnage actif ===")
            
            # Charger les données du compte depuis le fichier local
            if not os.path.exists('data/account.json'):
                self.logger.error("❌ Aucun compte trouvé dans data/account.json")
                return

            with open('data/account.json', 'r') as f:
                account_data = json.load(f)
                
            if not account_data.get('Response'):
                self.logger.error("❌ Données de compte invalides")
                return
            
            player_info = account_data['Response'][0]
            membership_id = player_info['membershipId']
            membership_type = player_info['membershipType']
            
            headers = {
                'X-API-Key': self.OAUTH_CONFIG['api_key']
            }
            
            # Modifier la requête pour inclure les instances
            profile_url = f'https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/'
            
            # Requête séparée pour les caractéristiques du personnage
            character_response = requests.get(
                profile_url,
                headers=headers,
                params={'components': '200'}  # Characters only
            )
            
            if character_response.status_code == 200:
                character_data = character_response.json()['Response']
                characters = character_data.get('characters', {}).get('data', {})
                
                if characters:
                    last_played_character = max(characters.items(), 
                        key=lambda x: x[1].get('dateLastPlayed', ''))
                    character_id = last_played_character[0]
                    
                    # Requête spécifique pour l'équipement du personnage
                    equipment_url = f'https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/Character/{character_id}/'
                    equipment_response = requests.get(
                        equipment_url,
                        headers=headers,
                        params={'components': '205,300,302,304,305'}  # Equipment and instances
                    )
                    
                    if equipment_response.status_code == 200:
                        equipment_data = equipment_response.json()['Response']
                        character_equipment = equipment_data.get('equipment', {}).get('data', {}).get('items', [])
                        instances = equipment_data.get('itemComponents', {}).get('instances', {}).get('data', {})
                        
                        # Associer les données d'instance à chaque item
                        for item in character_equipment:
                            instance_id = item.get('itemInstanceId')
                            if instance_id in instances:
                                item['instance'] = instances[instance_id]
                                self.logger.info(f"Item {item.get('itemHash')} - Instance trouvée avec puissance: {item['instance'].get('primaryStat', {}).get('value', 0)}")
                        
                        self.display_equipment(character_equipment)
                    else:
                        self.logger.error(f"Erreur lors de la récupération de l'équipement: {equipment_response.status_code}")
                else:
                    self.logger.error("Aucun personnage trouvé")
            else:
                self.logger.error(f"Erreur lors de la récupération du personnage: {character_response.status_code}")
            
        except Exception as e:
            self.logger.error(f"Erreur: {str(e)}")

    def load_item_details(self, item, slot):
        """Charge les détails d'un item depuis l'API Bungie."""
        try:
            item_hash = item.get('itemHash')
            if not item_hash:
                self.logger.error("Hash de l'item non trouvé")
                return

            # Vérifier le cache
            if item_hash in self.item_definitions_cache:
                self.update_item_display(slot, self.item_definitions_cache[item_hash], item)
                return

            # Faire la requête à l'API
            headers = self.get_auth_headers()
            url = f'https://www.bungie.net/Platform/Destiny2/Manifest/DestinyInventoryItemDefinition/{item_hash}/'
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                item_def = response.json()['Response']
                self.item_definitions_cache[item_hash] = item_def
                self.update_item_display(slot, item_def, item)
            else:
                self.logger.error(f"Erreur lors de la récupération des détails de l'item: {response.status_code}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des détails de l'item: {str(e)}")

    def update_item_display(self, slot, item_def, instance_data):
        try:
            layout = slot.layout()
            if not layout:
                self.logger.error("❌ Layout non trouvé")
                return

            icon_label = layout.itemAt(0).widget()
            item_hash = str(item_def.get('hash', ''))
            item_name = item_def.get('displayProperties', {}).get('name', 'Inconnu')
            
            self.logger.info(f"🔄 Mise à jour du slot pour {item_name}")
            
            # Vérifier le fichier image
            icon_filename = os.path.join('icons', f"{item_hash}.png")
            if not os.path.exists(icon_filename):
                self.logger.error(f"❌ Fichier image manquant: {icon_filename}")
                return
            
            # Vérifier la taille du fichier
            file_size = os.path.getsize(icon_filename)
            self.logger.info(f"📁 Taille du fichier {icon_filename}: {file_size} octets")
            
            if file_size == 0:
                self.logger.error("❌ Fichier image vide")
                return
            
            # Charger l'image
            pixmap = QPixmap(icon_filename)
            if pixmap.isNull():
                self.logger.error(f"❌ Échec du chargement du pixmap pour {icon_filename}")
                # Vérifier le format du fichier
                with open(icon_filename, 'rb') as f:
                    header = f.read(8)
                    self.logger.info(f"En-tête du fichier: {header.hex()}")
                return
            
            self.logger.info(f"📏 Dimensions originales: {pixmap.width()}x{pixmap.height()}")
            
            # Redimensionner
            scaled_pixmap = pixmap.scaled(
                64, 64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            if scaled_pixmap.isNull():
                self.logger.error("❌ Échec du redimensionnement")
                return
            
            self.logger.info(f"📏 Dimensions après redimensionnement: {scaled_pixmap.width()}x{scaled_pixmap.height()}")
            
            # Appliquer au label
            icon_label.setPixmap(scaled_pixmap)
            self.logger.info("✅ Image appliquée au label")

            # Mise à jour des autres informations
            power = instance_data.get('instance', {}).get('primaryStat', {}).get('value', 0)
            
            power_label = layout.itemAt(1).widget()
            power_label.setText(str(power))
            
            name_label = layout.itemAt(2).widget()
            name_label.setText(item_name)
            
            self.logger.info(f"✅ Mise à jour complète - {item_name} ({power})")

        except Exception as e:
            self.logger.error(f"❌ Erreur dans update_item_display: {str(e)}")
            self.logger.exception("Détails de l'erreur:")

    def verify_image_file(self, filename):
        """Vérifie si le fichier image est valide."""
        try:
            # Vérifier si le fichier existe
            if not os.path.exists(filename):
                self.logger.error(f"Fichier non trouvé: {filename}")
                return False
            
            # Vérifier la taille
            size = os.path.getsize(filename)
            if size == 0:
                self.logger.error(f"Fichier vide: {filename}")
                return False
            
            # Vérifier l'en-tête PNG
            with open(filename, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'\x89PNG\r\n\x1a\n'):
                    self.logger.error(f"Format invalide pour {filename}")
                    return False
                
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification de {filename}: {e}")
            return False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DestinyHub()
    window.show()
    sys.exit(app.exec()) 