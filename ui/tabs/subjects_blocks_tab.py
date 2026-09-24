import qtawesome as qta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QDialog,
    QFormLayout, QMessageBox, QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt
from models.subject import SubjectBlockModel

class BlockFormDialog(QDialog):
    def __init__(self, parent=None, block_data=None):
        super().__init__(parent)
        self.block_data = block_data
        self.setWindowTitle("Editar Bloco" if block_data else "Novo Bloco")
        self.setWindowIcon(qta.icon('fa5s.cubes', color='#242D64'))
        self.resize(340, 150)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        form = QFormLayout()

        self.txt_nome = QLineEdit()
        if self.block_data:
            self.txt_nome.setText(self.block_data["nome"])

        form.addRow("Nome do Bloco *:", self.txt_nome)
        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setIcon(qta.icon('fa5s.times', color='#242D64'))
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Salvar")
        btn_save.setIcon(qta.icon('fa5s.check', color='white'))
        btn_save.setObjectName("btnNavy")
        btn_save.clicked.connect(self.accept)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def get_data(self):
        return {"nome": self.txt_nome.text().strip()}


class SubjectFormDialog(QDialog):
    def __init__(self, model: SubjectBlockModel, parent=None, subject_data=None):
        super().__init__(parent)
        self.model = model
        self.subject_data = subject_data
        self.setWindowTitle("Editar Disciplina" if subject_data else "Nova Disciplina")
        self.setWindowIcon(qta.icon('fa5s.book-open', color='#242D64'))
        self.resize(380, 180)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        form = QFormLayout()

        self.txt_nome = QLineEdit()
        self.combo_bloco = QComboBox()
        self.combo_bloco.addItem("Nenhum Bloco", None)

        for b in self.model.list_blocks():
            self.combo_bloco.addItem(b["nome"], b["id"])

        if self.subject_data:
            self.txt_nome.setText(self.subject_data["nome"])
            bloco_id = self.subject_data.get("bloco_id")
            if bloco_id:
                idx = self.combo_bloco.findData(bloco_id)
                if idx >= 0:
                    self.combo_bloco.setCurrentIndex(idx)

        form.addRow("Nome da Disciplina *:", self.txt_nome)
        form.addRow("Pertence ao Bloco:", self.combo_bloco)
        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setIcon(qta.icon('fa5s.times', color='#242D64'))
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Salvar")
        btn_save.setIcon(qta.icon('fa5s.check', color='white'))
        btn_save.setObjectName("btnNavy")
        btn_save.clicked.connect(self.accept)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def get_data(self):
        return {
            "nome": self.txt_nome.text().strip(),
            "bloco_id": self.combo_bloco.currentData()
        }


class SubjectsBlocksTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = SubjectBlockModel()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel 1: Blocos
        panel_blocos = QGroupBox("Blocos de Disciplinas")
        l_blocos = QVBoxLayout(panel_blocos)

        h_b_actions = QHBoxLayout()
        btn_new_block = QPushButton("Novo Bloco")
        btn_new_block.setIcon(qta.icon('fa5s.plus', color='white'))
        btn_new_block.setObjectName("btnNavy")
        btn_new_block.clicked.connect(self.new_block)
        h_b_actions.addWidget(btn_new_block)
        h_b_actions.addStretch()
        l_blocos.addLayout(h_b_actions)

        self.tbl_blocos = QTableWidget()
        self.tbl_blocos.setAlternatingRowColors(True)
        self.tbl_blocos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_blocos.setColumnCount(3)
        self.tbl_blocos.setHorizontalHeaderLabels(["ID", "Nome do Bloco", "Ações"])
        self.tbl_blocos.verticalHeader().setDefaultSectionSize(44)
        self.tbl_blocos.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_blocos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_blocos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.tbl_blocos.setColumnWidth(2, 170)
        l_blocos.addWidget(self.tbl_blocos)

        splitter.addWidget(panel_blocos)

        # Panel 2: Disciplinas
        panel_disc = QGroupBox("Disciplinas Cadastradas")
        l_disc = QVBoxLayout(panel_disc)

        h_d_actions = QHBoxLayout()
        btn_new_subject = QPushButton("Nova Disciplina")
        btn_new_subject.setIcon(qta.icon('fa5s.plus', color='white'))
        btn_new_subject.setObjectName("btnNavy")
        btn_new_subject.clicked.connect(self.new_subject)
        h_d_actions.addWidget(btn_new_subject)
        h_d_actions.addStretch()
        l_disc.addLayout(h_d_actions)

        self.tbl_disc = QTableWidget()
        self.tbl_disc.setAlternatingRowColors(True)
        self.tbl_disc.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_disc.setColumnCount(4)
        self.tbl_disc.setHorizontalHeaderLabels(["ID", "Nome", "Bloco", "Ações"])
        self.tbl_disc.verticalHeader().setDefaultSectionSize(44)
        self.tbl_disc.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_disc.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_disc.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tbl_disc.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.tbl_disc.setColumnWidth(3, 170)
        l_disc.addWidget(self.tbl_disc)

        splitter.addWidget(panel_disc)

        main_layout.addWidget(splitter)

        self.load_data()

    def load_data(self):
        self.load_blocos()
        self.load_disciplinas()

    def load_blocos(self):
        blocks = self.model.list_blocks()
        self.tbl_blocos.setRowCount(len(blocks))

        for row_idx, b in enumerate(blocks):
            self.tbl_blocos.setItem(row_idx, 0, QTableWidgetItem(str(b["id"])))
            self.tbl_blocos.setItem(row_idx, 1, QTableWidgetItem(b["nome"]))

            btn_panel = QWidget()
            btn_layout = QHBoxLayout(btn_panel)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(6)

            btn_edit = QPushButton("Editar")
            btn_edit.setIcon(qta.icon('fa5s.edit', color='#242D64'))
            btn_edit.setObjectName("btnSecondary")
            btn_edit.setMinimumWidth(75)
            btn_edit.clicked.connect(lambda _, b_data=b: self.edit_block(b_data))

            btn_del = QPushButton("Excluir")
            btn_del.setIcon(qta.icon('fa5s.trash-alt', color='white'))
            btn_del.setObjectName("btnDanger")
            btn_del.setMinimumWidth(75)
            btn_del.clicked.connect(lambda _, b_id=b["id"], b_nome=b["nome"]: self.delete_block(b_id, b_nome))

            btn_layout.addWidget(btn_edit)
            btn_layout.addWidget(btn_del)
            self.tbl_blocos.setCellWidget(row_idx, 2, btn_panel)

    def load_disciplinas(self):
        subjects = self.model.list_subjects()
        self.tbl_disc.setRowCount(len(subjects))

        for row_idx, s in enumerate(subjects):
            self.tbl_disc.setItem(row_idx, 0, QTableWidgetItem(str(s["id"])))
            self.tbl_disc.setItem(row_idx, 1, QTableWidgetItem(s["nome"]))
            self.tbl_disc.setItem(row_idx, 2, QTableWidgetItem(s.get("bloco_nome") or "-"))

            btn_panel = QWidget()
            btn_layout = QHBoxLayout(btn_panel)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(6)

            btn_edit = QPushButton("Editar")
            btn_edit.setIcon(qta.icon('fa5s.edit', color='#242D64'))
            btn_edit.setObjectName("btnSecondary")
            btn_edit.setMinimumWidth(75)
            btn_edit.clicked.connect(lambda _, s_data=s: self.edit_subject(s_data))

            btn_del = QPushButton("Excluir")
            btn_del.setIcon(qta.icon('fa5s.trash-alt', color='white'))
            btn_del.setObjectName("btnDanger")
            btn_del.setMinimumWidth(75)
            btn_del.clicked.connect(lambda _, s_id=s["id"], s_nome=s["nome"]: self.delete_subject(s_id, s_nome))

            btn_layout.addWidget(btn_edit)
            btn_layout.addWidget(btn_del)
            self.tbl_disc.setCellWidget(row_idx, 3, btn_panel)

    def new_block(self):
        dlg = BlockFormDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                self.model.create_block(data["nome"])
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao criar bloco: {str(e)}")

    def edit_block(self, block_data):
        dlg = BlockFormDialog(self, block_data=block_data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                self.model.update_block(block_data["id"], data["nome"])
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao atualizar bloco: {str(e)}")

    def delete_block(self, block_id: int, block_nome: str):
        reply = QMessageBox.question(
            self, "Confirmar Exclusão", f"Deseja excluir o bloco '{block_nome}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.model.delete_block(block_id)
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir bloco: {str(e)}")

    def new_subject(self):
        dlg = SubjectFormDialog(self.model, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                self.model.create_subject(data["nome"], data["bloco_id"])
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao criar disciplina: {str(e)}")

    def edit_subject(self, subject_data):
        dlg = SubjectFormDialog(self.model, self, subject_data=subject_data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                self.model.update_subject(subject_data["id"], data["nome"], data["bloco_id"])
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao atualizar disciplina: {str(e)}")

    def delete_subject(self, subject_id: int, subject_nome: str):
        reply = QMessageBox.question(
            self, "Confirmar Exclusão", f"Deseja excluir a disciplina '{subject_nome}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.model.delete_subject(subject_id)
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir disciplina: {str(e)}")
