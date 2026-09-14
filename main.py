import sys
from PyQt6.QtWidgets import QApplication
from ui.theme import apply_theme
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Corretor de Provas")
    apply_theme(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
