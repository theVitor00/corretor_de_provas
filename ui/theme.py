from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QApplication

NAVY_MAIN = "#242D64"
TEAL_ACCENT = "#00A9A4"
TEAL_LIGHT = "#E6F7F7"
WHITE = "#FFFFFF"
BG_MAIN = "#F8FAFC"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E2E8F0"
TEXT_MAIN = "#1E293B"
TEXT_MUTED = "#64748B"
SUCCESS_COLOR = "#10B981"
DANGER_COLOR = "#EF4444"

QSS_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #F8FAFC;
    color: #1E293B;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}

QWidget {
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    color: #1E293B;
}

QTabWidget::pane {
    border: 1px solid #E2E8F0;
    background: #FFFFFF;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background: #F1F5F9;
    border: 1px solid #E2E8F0;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 10px 18px;
    margin-right: 4px;
    font-weight: 600;
    color: #64748B;
}

QTabBar::tab:selected {
    background: #242D64;
    color: #FFFFFF;
    border-color: #242D64;
}

QTabBar::tab:hover:!selected {
    background: #E2E8F0;
    color: #242D64;
}

QPushButton {
    background-color: #00A9A4;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #008D89;
}

QPushButton:pressed {
    background-color: #007370;
}

QPushButton#btnNavy {
    background-color: #242D64;
    color: #FFFFFF;
}

QPushButton#btnNavy:hover {
    background-color: #1A214A;
}

QPushButton#btnSecondary {
    background-color: #F1F5F9;
    color: #242D64;
    border: 1px solid #CBD5E1;
}

QPushButton#btnSecondary:hover {
    background-color: #E2E8F0;
}

QPushButton#btnDanger {
    background-color: #EF4444;
    color: #FFFFFF;
}

QPushButton#btnDanger:hover {
    background-color: #DC2626;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 7px 10px;
    color: #1E293B;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1.5px solid #00A9A4;
}

QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    gridline-color: #F1F5F9;
    border-radius: 6px;
    selection-background-color: #E6F7F7;
    selection-color: #242D64;
}

QHeaderView::section {
    background-color: #242D64;
    color: #FFFFFF;
    padding: 8px;
    font-weight: 600;
    border: none;
}

QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 14px;
    font-weight: bold;
    color: #242D64;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 5px;
    background-color: #FFFFFF;
}

QProgressBar {
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    text-align: center;
    background-color: #F1F5F9;
}

QProgressBar::chunk {
    background-color: #00A9A4;
    border-radius: 5px;
}
"""

def apply_theme(app: QApplication):
    app.setStyleSheet(QSS_STYLESHEET)
