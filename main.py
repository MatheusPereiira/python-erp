import sys
from PyQt6.QtWidgets import QApplication

from main_app import MainWindow, aplicar_tema_calmo 

if __name__ == "__main__":

    
    app = QApplication(sys.argv)
    aplicar_tema_calmo(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
    