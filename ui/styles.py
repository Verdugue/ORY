from PyQt6.QtGui import QPalette, QColor

def setup_dark_theme(app):
    """Configure le thème sombre de l'application."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(18, 20, 23))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(236, 236, 236))
    palette.setColor(QPalette.ColorRole.Base, QColor(28, 30, 34))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(35, 37, 41))
    palette.setColor(QPalette.ColorRole.Text, QColor(236, 236, 236))
    palette.setColor(QPalette.ColorRole.Button, QColor(35, 37, 41))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(236, 236, 236))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(77, 122, 255))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    
    app.setPalette(palette)

GLOBAL_STYLE = """
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
"""