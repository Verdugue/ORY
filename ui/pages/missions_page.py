from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QScrollArea, QGroupBox)
from PyQt6.QtCore import Qt, QTimer
import logging
import psutil

class MissionsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # En-tête avec statut
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
        
        # Message par défaut
        self.no_missions_label = QLabel("Aucune mission active\nLancez Destiny 2 pour voir vos missions")
        self.no_missions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.missions_layout.addWidget(self.no_missions_label)
        
        scroll_area.setWidget(missions_widget)
        layout.addWidget(scroll_area)

    def setup_timer(self):
        self.game_check_timer = QTimer()
        self.game_check_timer.timeout.connect(self.check_game_status)
        self.game_check_timer.start(5000)  # Vérifier toutes les 5 secondes

    def check_game_status(self):
        try:
            destiny2_running = False
            for process in psutil.process_iter(['name']):
                if process.info['name'] == 'destiny2.exe':
                    destiny2_running = True
                    break
            
            if destiny2_running:
                self.game_status_label.setText("Statut de Destiny 2: En cours d'exécution")
                self.game_status_label.setStyleSheet("color: green;")
                self.update_missions()
            else:
                self.game_status_label.setText("Statut de Destiny 2: Non détecté")
                self.game_status_label.setStyleSheet("color: red;")
                self.no_missions_label.show()
                
        except Exception as e:
            logging.error(f"Erreur lors de la vérification du statut du jeu: {str(e)}")

    def update_missions(self):
        try:
            self.no_missions_label.hide()
            
            # Nettoyer les anciennes missions
            while self.missions_layout.count() > 1:
                item = self.missions_layout.takeAt(1)
                if item.widget():
                    item.widget().deleteLater()
            
            # Exemple de missions (à remplacer par les vraies données)
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
            
            for mission in test_missions:
                self.add_mission(mission)
                
        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour des missions: {str(e)}")

    def add_mission(self, mission):
        mission_group = QGroupBox(mission['name'])
        layout = QVBoxLayout()
        
        description = QLabel(mission['description'])
        description.setWordWrap(True)
        layout.addWidget(description)
        
        progress = QLabel(f"Progression: {mission['progress']}")
        progress.setStyleSheet("color: #2a82da;")
        layout.addWidget(progress)
        
        mission_group.setLayout(layout)
        self.missions_layout.addWidget(mission_group)