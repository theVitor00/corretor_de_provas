import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QGroupBox, QFileDialog, QMessageBox, QFormLayout
)
from PyQt6.QtGui import QPixmap
from database import Database, db as default_db

class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = default_db
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Branding Card
        gb_branding = QGroupBox("Personalização de Relatórios (Logotipo e Marca d'Água)")
        f_brand = QFormLayout(gb_branding)

        h_logo = QHBoxLayout()
        self.txt_logo_path = QLineEdit()
        self.txt_logo_path.setReadOnly(True)

        btn_browse_logo = QPushButton("Selecionar Imagem...")
        btn_browse_logo.setObjectName("btnNavy")
        btn_browse_logo.clicked.connect(self.browse_logo)

        btn_clear_logo = QPushButton("Remover Logo")
        btn_clear_logo.setObjectName("btnSecondary")
        btn_clear_logo.clicked.connect(self.clear_logo)

        h_logo.addWidget(self.txt_logo_path)
        h_logo.addWidget(btn_browse_logo)
        h_logo.addWidget(btn_clear_logo)

        self.lbl_logo_preview = QLabel("Sem logotipo configurado")
        self.lbl_logo_preview.setFixedHeight(80)
        self.lbl_logo_preview.setStyleSheet("border: 1px dashed #CBD5E1; background: #FFFFFF;")

        self.txt_watermark = QLineEdit()
        self.txt_watermark.setPlaceholderText("Texto da marca d'água no fundo do PDF (ex: CORRETOR DE PROVAS)")

        f_brand.addRow("Logotipo da Instituição:", h_logo)
        f_brand.addRow("Pré-visualização do Logo:", self.lbl_logo_preview)
        f_brand.addRow("Texto da Marca d'Água:", self.txt_watermark)

        layout.addWidget(gb_branding)

        # Save Action
        h_btn = QHBoxLayout()
        btn_save = QPushButton("💾 Salvar Configurações")
        btn_save.setObjectName("btnNavy")
        btn_save.clicked.connect(self.save_settings)
        h_btn.addWidget(btn_save)
        h_btn.addStretch()

        layout.addLayout(h_btn)
        layout.addStretch()

        self.load_settings()

    def load_settings(self):
        logo_path = self.db.get_config("logo_path", "")
        watermark = self.db.get_config("watermark_text", "CORRETOR DE PROVAS")

        self.txt_logo_path.setText(logo_path)
        self.txt_watermark.setText(watermark)

        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                scaled = pixmap.scaledToHeight(70, Qt.TransformationMode.SmoothTransformation)
                self.lbl_logo_preview.setPixmap(scaled)
            else:
                self.lbl_logo_preview.setText("Imagem de logo inválida.")
        else:
            self.lbl_logo_preview.setText("Nenhum logotipo selecionado.")

    def browse_logo(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Logotipo da Instituição", "", "Imagens (*.png *.jpg *.jpeg *.bmp)"
        )
        if filepath:
            self.txt_logo_path.setText(filepath)
            pixmap = QPixmap(filepath)
            if not pixmap.isNull():
                scaled = pixmap.scaledToHeight(70, Qt.TransformationMode.SmoothTransformation)
                self.lbl_logo_preview.setPixmap(scaled)

    def clear_logo(self):
        self.txt_logo_path.clear()
        self.lbl_logo_preview.setText("Nenhum logotipo selecionado.")

    def save_settings(self):
        logo_path = self.txt_logo_path.text().strip()
        watermark = self.txt_watermark.text().strip()

        try:
            self.db.set_config("logo_path", logo_path)
            self.db.set_config("watermark_text", watermark)
            QMessageBox.information(self, "Sucesso", "Configurações salvas com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar configurações:\n{str(e)}")
