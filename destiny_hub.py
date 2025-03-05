from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLineEdit, QLabel, 
                           QStackedWidget, QTextEdit, QMessageBox, QTableWidget, 
                           QTableWidgetItem, QHeaderView, QSplitter, QPlainTextEdit)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
import sys
import requests
import json
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

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

class DestinyHub(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Destiny 2 Hub")
        self.setMinimumSize(1000, 600)
        
        # Load Bungie API key from environment variable
        self.api_key = os.getenv('BUNGIE_API_KEY')
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # Create and setup navigation panel
        self.setup_navigation_panel(main_layout)
        
        # Create and setup main content area
        self.setup_main_content(main_layout)
        
        # Style the application
        self.setup_styles()

        # Configurer le handler de logging personnalisé
        self.log_handler = ErrorLogHandler(self.handle_log)
        logging.getLogger().addHandler(self.log_handler)

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
        
        # Welcome message
        welcome_label = QLabel("Welcome to Destiny 2 Hub")
        welcome_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)
        
        # Description
        desc_label = QLabel("Connect your Destiny 2 account to view your stats and inventory")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        # API Key input
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your Bungie API Key")
        layout.addWidget(self.api_key_input)
        
        # Save button
        save_btn = QPushButton("Save API Key")
        save_btn.clicked.connect(self.save_api_key)
        layout.addWidget(save_btn)
        
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

    def save_api_key(self):
        try:
            api_key = self.api_key_input.text()
            if api_key:
                with open('.env', 'w') as f:
                    f.write(f'BUNGIE_API_KEY={api_key}')
                self.api_key = api_key
                logging.info("API Key saved successfully")
                QMessageBox.information(self, "Success", "API Key saved successfully!")
            else:
                logging.warning("Attempted to save empty API Key")
                QMessageBox.warning(self, "Error", "Please enter an API Key")
        except Exception as e:
            logging.error(f"Failed to save API Key: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to save API Key: {str(e)}")

    def search_profile(self):
        try:
            if not self.api_key:
                logging.warning("Profile search attempted without API Key")
                QMessageBox.warning(self, "Error", "Please set your API Key first")
                return

            bungie_name = self.bungie_name_input.text()
            if not bungie_name or '#' not in bungie_name:
                logging.warning(f"Invalid Bungie Name format: {bungie_name}")
                QMessageBox.warning(self, "Error", "Please enter a valid Bungie Name (e.g., Guardian#1234)")
                return

            display_name, display_name_code = bungie_name.split('#')
            
            # Log the search attempt
            logging.info(f"Searching for player: {display_name}#{display_name_code}")
            
            headers = {
                'X-API-Key': self.api_key,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
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
                        self.display_profile_info(profile_data)
                    else:
                        QMessageBox.warning(self, "Error", "Failed to fetch profile details")
                else:
                    QMessageBox.warning(self, "Error", "Player not found")
            else:
                QMessageBox.warning(self, "Error", "Failed to search for player")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"An error occurred: {str(e)}")

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

    def handle_log(self, record):
        # Cette méthode est appelée pour chaque nouveau log
        if self.error_log_page.auto_refresh.isChecked():
            self.error_log_page.refresh_logs()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DestinyHub()
    window.show()
    sys.exit(app.exec()) 