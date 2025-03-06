import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import DestinyHub
from src.utils.logger import setup_logging

def main():
    setup_logging()
    app = QApplication(sys.argv)
    window = DestinyHub()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 