import sys
import os

# Ensure local imports work correctly when packaged
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from data.db import init_db
from gui.main_window import MainWindow

def main():
    # Initialize SQLite schema
    init_db()
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Run the Main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
