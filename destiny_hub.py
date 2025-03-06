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
        
        # Initialiser les configurations OAuth et API
        self.OAUTH_CONFIG = {
            'client_id': '49198',  # Votre client_id de Bungie
            'api_key': os.getenv('BUNGIE_API_KEY'),  # Charger depuis .env
            'auth_url': 'https://www.bungie.net/en/OAuth/Authorize',
            'token_url': 'https://www.bungie.net/Platform/App/OAuth/token/',
            'redirect_uri': 'https://ory.ovh/'
        }
        
        # Initialiser le logger avant l'interface
        self.setup_logging()
        
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
        # Set dark theme palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        
        QApplication.instance().setPalette(palette)
        
        # Set stylesheet for buttons
        button_style = """
            QPushButton {
                background-color: #2a82da;
                border: none;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3292ea;
            }
            QPushButton:pressed {
                background-color: #1a72ca;
            }
        """
        
        # Set stylesheet for text inputs
        input_style = """
            QLineEdit {
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #555;
                background-color: #333;
                color: white;
            }
            QTextEdit {
                border-radius: 5px;
                border: 1px solid #555;
                background-color: #333;
                color: white;
            }
        """
        
        self.setStyleSheet(button_style + input_style)

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
        """Met à jour l'affichage du statut de la session."""
        if self.access_token and self.user_profile:
            self.session_label.setText("Session active - Profil chargé")
            self.session_label.setStyleSheet("color: green")
        elif self.access_token:
            self.session_label.setText("Session active - Profil non chargé")
            self.session_label.setStyleSheet("color: orange")
        else:
            self.session_label.setText("Aucune session active")
            self.session_label.setStyleSheet("color: red")

    def handle_log(self, message):
        """Gestion sûre des logs dans l'interface."""
        try:
            if hasattr(self, 'error_log_page') and not self.error_log_page.isHidden():
                self.error_log_page.log_text.append(message)
        except Exception:
            pass  # Ignorer silencieusement les erreurs d'interface

    def setup_logging(self):
        """Configure le système de logging de manière sûre."""
        class SafeQtHandler(logging.Handler):
            def __init__(self, callback):
                super().__init__()
                self.callback = callback

            def emit(self, record):
                try:
                    QMetaObject.invokeMethod(self, 
                                           "handle_log_safely",
                                           Qt.ConnectionType.QueuedConnection,
                                           Q_ARG(str, self.format(record)))
                except Exception:
                    pass

            @pyqtSlot(str)
            def handle_log_safely(self, message):
                try:
                    if hasattr(self, 'callback'):
                        self.callback(message)
                except Exception:
                    pass

        # Configuration du logger
        self.logger = logging.getLogger('DestinyHub')
        self.logger.setLevel(logging.INFO)
        
        # Ajouter le handler Qt de manière sûre
        handler = SafeQtHandler(self.handle_log)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

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
        """Crée la page d'équipement style Destiny 2."""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Style pour les widgets d'équipement
        equipment_style = """
            QWidget#equipment_slot {
                background-color: rgba(0, 0, 0, 0.7);
                border: 1px solid #444;
                border-radius: 5px;
                padding: 5px;
            }
            QLabel#power {
                color: #FFEB3B;
                font-size: 16px;
                font-weight: bold;
            }
            QLabel#item_name {
                color: white;
                font-size: 12px;
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
            armor_column.addWidget(slot)
            self.armor_slots.append(slot)
        
        armor_column.addStretch()

        # Ajouter les colonnes au layout principal
        layout.addLayout(weapons_column)
        layout.addWidget(character_widget)
        layout.addLayout(armor_column)

        return page

    def display_equipment(self, equipment):
        """Affiche l'équipement dans le style Destiny 2."""
        try:
            # Trier l'équipement par type
            sorted_equipment = {
                'weapons': [],
                'armor': []
            }

            # Calculer la puissance totale
            total_power = 0
            valid_items = 0

            for item in equipment:
                # Récupérer la puissance de l'item
                power = item.get('instance', {}).get('primaryStat', {}).get('value', 0)
                if power > 0:
                    total_power += power
                    valid_items += 1

                bucket_type = self.get_bucket_type(str(item.get('bucketHash', '')))
                if bucket_type in ['kinetic', 'energy', 'power']:
                    sorted_equipment['weapons'].append(item)
                elif bucket_type in ['helmet', 'gauntlets', 'chest', 'legs', 'class_item']:
                    sorted_equipment['armor'].append(item)

            # Mettre à jour les slots d'armes
            for i, slot in enumerate(self.weapon_slots):
                if i < len(sorted_equipment['weapons']):
                    self.update_equipment_slot(slot, sorted_equipment['weapons'][i])

            # Mettre à jour les slots d'armure
            for i, slot in enumerate(self.armor_slots):
                if i < len(sorted_equipment['armor']):
                    self.update_equipment_slot(slot, sorted_equipment['armor'][i])

            # Mettre à jour le niveau de puissance total
            if valid_items > 0:
                average_power = total_power // valid_items
                self.power_value.setText(str(average_power))
            else:
                self.power_value.setText("0")

        except Exception as e:
            self.logger.error(f"Erreur affichage équipement: {str(e)}")

    def update_equipment_slot(self, slot, item):
        """Met à jour un slot d'équipement avec les informations de l'item."""
        try:
            # Obtenir le layout existant ou en créer un nouveau si nécessaire
            layout = slot.layout()
            if not layout:
                layout = QVBoxLayout(slot)
                layout.setContentsMargins(5, 5, 5, 5)
            
            # Nettoyer le layout existant
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # Icône de l'item
            icon_label = QLabel()
            icon_label.setFixedSize(64, 64)
            layout.addWidget(icon_label)
            
            # Niveau de puissance
            power_label = QLabel(str(item.get('primaryStat', {}).get('value', 0)))
            power_label.setObjectName("power")
            power_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(power_label)
            
            # Nom de l'item
            name_label = QLabel("Chargement...")
            name_label.setObjectName("item_name")
            name_label.setWordWrap(True)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(name_label)
            
            # Charger les détails de l'item
            self.load_item_details(item, slot)
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour slot: {str(e)}")

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
            
            # Vérifier le format du Bungie Name
            if not bungie_name or '#' not in bungie_name:
                self.logger.warning("Format de Bungie Name invalide")
                QMessageBox.warning(self, "Erreur", "Format de Bungie Name invalide (ex: Guardian#1234)")
                return

            display_name, display_name_code = bungie_name.split('#')
            
            # S'assurer que le code est un nombre
            try:
                display_name_code = int(display_name_code)
            except ValueError:
                self.logger.warning("Code du Bungie Name invalide")
                QMessageBox.warning(self, "Erreur", "Le code du Bungie Name doit être un nombre")
                return
            
            # Vérifier la clé API
            if not self.OAUTH_CONFIG['api_key']:
                self.logger.error("Clé API manquante")
                QMessageBox.warning(self, "Erreur", "Clé API Bungie non configurée")
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
        
        # Initialiser les configurations OAuth et API
        self.OAUTH_CONFIG = {
            'client_id': '49198',  # Votre client_id de Bungie
            'api_key': os.getenv('BUNGIE_API_KEY'),  # Charger depuis .env
            'auth_url': 'https://www.bungie.net/en/OAuth/Authorize',
            'token_url': 'https://www.bungie.net/Platform/App/OAuth/token/',
            'redirect_uri': 'https://ory.ovh/'
        }
        
        # Initialiser le logger avant l'interface
        self.setup_logging()
        
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
        # Set dark theme palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        
        QApplication.instance().setPalette(palette)
        
        # Set stylesheet for buttons
        button_style = """
            QPushButton {
                background-color: #2a82da;
                border: none;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3292ea;
            }
            QPushButton:pressed {
                background-color: #1a72ca;
            }
        """
        
        # Set stylesheet for text inputs
        input_style = """
            QLineEdit {
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #555;
                background-color: #333;
                color: white;
            }
            QTextEdit {
                border-radius: 5px;
                border: 1px solid #555;
                background-color: #333;
                color: white;
            }
        """
        
        self.setStyleSheet(button_style + input_style)

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

    def validate_api_key(self):
        """Valide la clé API avec une requête simple."""
                return
            
            # Préparer les headers pour l'API
            headers = self.get_auth_headers()
            
            # Log les headers (sans la clé API)
            self.logger.debug(f"Headers de requête: {headers}")
            
            # Données pour la recherche
        try:
            headers = {'X-API-Key': self.OAUTH_CONFIG['api_key']}
            search_data = {
                'displayName': display_name,
                'displayNameCode': display_name_code
            }
            
            # Log la requête
            self.logger.info(f"Recherche du joueur: {display_name}#{display_name_code}")
            
            # Rechercher le joueur
            response = requests.post(
                response = requests.get(
                    f'https://www.bungie.net/Platform/Destiny2/Manifest/DestinyInventoryItemDefinition/{item_hash}/',
                    headers=headers
                )
                
                if response.status_code == 200:
                    item_def = response.json()['Response']
                    self.item_definitions_cache[item_hash] = item_def
                else:
                    self.logger.error(f"Erreur lors de la récupération des détails de l'item: {response.status_code}")
                    return

            # Mettre à jour le nom de l'item
            name_label = slot.findChild(QLabel, "item_name")
            if name_label:
                name_label.setText(item_def.get('displayProperties', {}).get('name', 'Inconnu'))

            # Télécharger et afficher l'icône
            icon_path = item_def.get('displayProperties', {}).get('icon')
            if icon_path:
                local_icon_path = f"data/icons/{item_hash}.png"
                
                # Vérifier si l'icône existe déjà
                if not os.path.exists(local_icon_path):
                    icon_url = f"https://www.bungie.net{icon_path}"
                    icon_response = requests.get(icon_url)
                    if icon_response.status_code == 200:
                        with open(local_icon_path, 'wb') as f:
                            f.write(icon_response.content)

                # Afficher l'icône
                icon_label = slot.findChild(QLabel)
                if icon_label and os.path.exists(local_icon_path):
                    pixmap = QPixmap(local_icon_path)
                    icon_label.setPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio))

        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des détails de l'item: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DestinyHub()
    window.show()
    sys.exit(app.exec()) 