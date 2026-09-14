from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QDialog,
    QFormLayout, QMessageBox, QGroupBox, QSpinBox, QDoubleSpinBox,
    QDateEdit, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QDate
from models.exam import ExamModel
from models.subject import SubjectBlockModel

class SubjectRangeDialog(QDialog):
    def __init__(self, subjects_list, total_questions, parent=None):
        super().__init__(parent)
        self.subjects_list = subjects_list
        self.total_questions = total_questions
        self.setWindowTitle("Adicionar Mapeamento de Disciplina")
        self.resize(340, 180)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.combo_subject = QComboBox()
        for s in self.subjects_list:
            self.combo_subject.addItem(s["nome"], s)

        self.spin_start = QSpinBox()
        self.spin_start.setRange(1, max(1, self.total_questions))
        self.spin_start.setValue(1)

        self.spin_end = QSpinBox()
        self.spin_end.setRange(1, max(1, self.total_questions))
        self.spin_end.setValue(max(1, self.total_questions))

        form.addRow("Disciplina:", self.combo_subject)
        form.addRow("Questão Inicial:", self.spin_start)
        form.addRow("Questão Final:", self.spin_end)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)

        btn_add = QPushButton("Adicionar")
        btn_add.setObjectName("btnNavy")
        btn_add.clicked.connect(self.validate_and_accept)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_add)
        layout.addLayout(btn_box)

    def validate_and_accept(self):
        if self.spin_start.value() > self.spin_end.value():
            QMessageBox.warning(self, "Aviso", "A questão inicial não pode ser maior que a questão final.")
            return
        self.accept()

    def get_data(self):
        s_data = self.combo_subject.currentData()
        return {
            "subject_id": s_data["id"],
            "nome": s_data["nome"],
            "start_q": self.spin_start.value(),
            "end_q": self.spin_end.value()
        }


class ExamFormDialog(QDialog):
    def __init__(self, exam_model: ExamModel, subject_model: SubjectBlockModel, parent=None, exam_data=None):
        super().__init__(parent)
        self.exam_model = exam_model
        self.subject_model = subject_model
        self.exam_data = exam_data
        self.setWindowTitle("Editar Prova" if exam_data else "Nova Prova")
        self.resize(750, 580)
        self.gabaritos_map = {}  # {"1": "ABCDE...", "2": "..."}
        self.mapped_subjects = [] # [{"nome": "Matemática", "start_q": 1, "end_q": 10}]
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Dados Básicos
        gb_basic = QGroupBox("Dados Básicos da Prova")
        f_basic = QFormLayout(gb_basic)

        self.txt_nome = QLineEdit()
        self.txt_data = QDateEdit()
        self.txt_data.setDate(QDate.currentDate())
        self.txt_data.setCalendarPopup(True)

        self.combo_bloco = QComboBox()
        self.combo_bloco.addItem("Nenhum Bloco", None)
        for b in self.subject_model.list_blocks():
            self.combo_bloco.addItem(b["nome"], b["id"])

        self.spin_valor = QDoubleSpinBox()
        self.spin_valor.setRange(1.0, 1000.0)
        self.spin_valor.setValue(10.0)
        self.spin_valor.setSingleStep(1.0)

        f_basic.addRow("Nome da Prova *:", self.txt_nome)
        f_basic.addRow("Data da Prova *:", self.txt_data)
        f_basic.addRow("Bloco de Disciplinas:", self.combo_bloco)
        f_basic.addRow("Valor Total (Pontos):", self.spin_valor)
        layout.addWidget(gb_basic)

        # Tipos e Gabaritos
        gb_gab = QGroupBox("Tipos de Prova e Gabaritos (Obrigatoriamente 1 Gabarito por Tipo)")
        l_gab = QVBoxLayout(gb_gab)

        h_g_controls = QHBoxLayout()
        self.txt_tipo = QLineEdit()
        self.txt_tipo.setPlaceholderText("Tipo (ex: 1, 2, A, B)")
        self.txt_tipo.setMaximumWidth(120)

        self.txt_gabarito = QLineEdit()
        self.txt_gabarito.setPlaceholderText("Sequência de Gabarito (ex: ABCDEABCDE...)")

        btn_add_gab = QPushButton("+ Adicionar Gabarito")
        btn_add_gab.setObjectName("btnNavy")
        btn_add_gab.clicked.connect(self.add_gabarito)

        h_g_controls.addWidget(QLabel("Tipo:"))
        h_g_controls.addWidget(self.txt_tipo)
        h_g_controls.addWidget(QLabel("Gabarito:"))
        h_g_controls.addWidget(self.txt_gabarito)
        h_g_controls.addWidget(btn_add_gab)
        l_gab.addLayout(h_g_controls)

        self.tbl_gabaritos = QTableWidget()
        self.tbl_gabaritos.setColumnCount(3)
        self.tbl_gabaritos.setHorizontalHeaderLabels(["Tipo", "Respostas do Gabarito", "Ação"])
        self.tbl_gabaritos.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_gabaritos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_gabaritos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        l_gab.addWidget(self.tbl_gabaritos)

        layout.addWidget(gb_gab)

        # Mapeamento por Disciplinas
        gb_map = QGroupBox("Mapeamento Posicional por Disciplina (Customização de Leitura)")
        l_map = QVBoxLayout(gb_map)

        h_m_controls = QHBoxLayout()
        btn_add_map = QPushButton("+ Definir Faixa de Questões por Disciplina")
        btn_add_map.setObjectName("btnSecondary")
        btn_add_map.clicked.connect(self.add_subject_mapping)
        h_m_controls.addWidget(btn_add_map)
        l_map.addLayout(h_m_controls)

        self.list_map = QListWidget()
        l_map.addWidget(self.list_map)

        layout.addWidget(gb_map)

        # Populate if editing
        if self.exam_data:
            self.txt_nome.setText(self.exam_data["nome"])
            q_date = QDate.fromString(self.exam_data["data"], "yyyy-MM-dd")
            if q_date.isValid():
                self.txt_data.setDate(q_date)
            
            bloco_id = self.exam_data.get("bloco_id")
            if bloco_id:
                idx = self.combo_bloco.findData(bloco_id)
                if idx >= 0:
                    self.combo_bloco.setCurrentIndex(idx)

            self.spin_valor.setValue(float(self.exam_data.get("valor_total", 10.0)))
            self.gabaritos_map = self.exam_data.get("gabaritos", {})
            self.mapped_subjects = self.exam_data.get("layout_config", {}).get("subjects", [])
            self.refresh_gabaritos_table()
            self.refresh_mapped_subjects_list()

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Salvar Prova")
        btn_save.setObjectName("btnNavy")
        btn_save.clicked.connect(self.validate_and_save)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def add_gabarito(self):
        tipo = self.txt_tipo.text().strip()
        gab = self.txt_gabarito.text().strip().upper()

        if not tipo or not gab:
            QMessageBox.warning(self, "Aviso", "Preencha o Tipo e a sequência do Gabarito.")
            return

        # Verificar se os gabaritos existentes possuem o mesmo tamanho
        if self.gabaritos_map:
            existing_len = len(next(iter(self.gabaritos_map.values())))
            if len(gab) != existing_len:
                QMessageBox.warning(
                    self, "Aviso", 
                    f"O gabarito informado possui {len(gab)} questões, mas o tamanho esperado para esta prova é {existing_len} questões."
                )
                return

        self.gabaritos_map[tipo] = gab
        self.txt_tipo.clear()
        self.txt_gabarito.clear()
        self.refresh_gabaritos_table()

    def remove_gabarito(self, tipo: str):
        if tipo in self.gabaritos_map:
            del self.gabaritos_map[tipo]
            self.refresh_gabaritos_table()

    def refresh_gabaritos_table(self):
        self.tbl_gabaritos.setRowCount(len(self.gabaritos_map))
        for row_idx, (tipo, gab) in enumerate(self.gabaritos_map.items()):
            self.tbl_gabaritos.setItem(row_idx, 0, QTableWidgetItem(tipo))
            self.tbl_gabaritos.setItem(row_idx, 1, QTableWidgetItem(f"{gab} ({len(gab)} Qs)"))

            btn_del = QPushButton("Remover")
            btn_del.setObjectName("btnDanger")
            btn_del.clicked.connect(lambda _, t=tipo: self.remove_gabarito(t))
            self.tbl_gabaritos.setCellWidget(row_idx, 2, btn_del)

    def add_subject_mapping(self):
        if not self.gabaritos_map:
            QMessageBox.warning(self, "Aviso", "Cadastre ao menos um tipo de gabarito antes de mapear disciplinas.")
            return

        num_q = len(next(iter(self.gabaritos_map.values())))
        all_subjects = self.subject_model.list_subjects()
        if not all_subjects:
            QMessageBox.warning(self, "Aviso", "Nenhuma disciplina cadastrada no sistema. Cadastre disciplinas na aba 'Disciplinas e Blocos'.")
            return

        dlg = SubjectRangeDialog(all_subjects, num_q, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            self.mapped_subjects.append(data)
            self.refresh_mapped_subjects_list()

    def refresh_mapped_subjects_list(self):
        self.list_map.clear()
        for idx, m in enumerate(self.mapped_subjects):
            text = f"• {m['nome']}: Questão {m['start_q']} até Questão {m['end_q']}"
            item = QListWidgetItem(text)
            self.list_map.addItem(item)

    def validate_and_save(self):
        nome = self.txt_nome.text().strip()
        data = self.txt_data.date().toString("yyyy-MM-dd")
        bloco_id = self.combo_bloco.currentData()
        valor_total = self.spin_valor.value()

        if not nome or not data:
            QMessageBox.warning(self, "Campos Obrigatórios", "Informe o Nome e a Data da prova.")
            return

        if not self.gabaritos_map:
            QMessageBox.warning(self, "Gabarito Obrigatório", "A prova precisa ter ao menos um tipo de gabarito cadastrado.")
            return

        layout_config = {
            "subjects": self.mapped_subjects
        }

        try:
            if self.exam_data:
                self.exam_model.update_exam(
                    self.exam_data["id"], nome, data, self.gabaritos_map,
                    bloco_id=bloco_id, valor_total=valor_total, layout_config=layout_config
                )
            else:
                self.exam_model.create_exam(
                    nome, data, self.gabaritos_map,
                    bloco_id=bloco_id, valor_total=valor_total, layout_config=layout_config
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar Prova", str(e))


class ExamsTab(QWidget):
    def __init__(self, on_process_request=None, on_view_results_request=None, parent=None):
        super().__init__(parent)
        self.exam_model = ExamModel()
        self.subject_model = SubjectBlockModel()
        self.on_process_request = on_process_request
        self.on_view_results_request = on_view_results_request
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header Bar
        h_bar = QHBoxLayout()
        btn_new_exam = QPushButton("+ Cadastrar Nova Prova")
        btn_new_exam.setObjectName("btnNavy")
        btn_new_exam.clicked.connect(self.new_exam)
        h_bar.addWidget(btn_new_exam)
        h_bar.addStretch()
        layout.addLayout(h_bar)

        # Exam Table / History
        gb_history = QGroupBox("Histórico de Provas Cadastradas")
        l_hist = QVBoxLayout(gb_history)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Data", "Nome da Prova", "Bloco", "Tipos de Gabarito", "Total Alunos", "Ações"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        l_hist.addWidget(self.table)
        layout.addWidget(gb_history)

        self.load_exams()

    def load_exams(self):
        exams = self.exam_model.list_exams()
        self.table.setRowCount(len(exams))

        for row_idx, e in enumerate(exams):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(e["id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(e["data"])))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(e["nome"])))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(e.get("bloco_nome") or "-")))
            
            tipos_str = ", ".join(e.get("gabaritos", {}).keys())
            self.table.setItem(row_idx, 4, QTableWidgetItem(tipos_str))
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(e.get("total_processados", 0))))

            btn_panel = QWidget()
            btn_layout = QHBoxLayout(btn_panel)
            btn_layout.setContentsMargins(2, 2, 2, 2)

            btn_proc = QPushButton("Processar .DAT")
            btn_proc.setObjectName("btnNavy")
            btn_proc.clicked.connect(lambda _, e_id=e["id"]: self.process_exam(e_id))

            btn_res = QPushButton("Resultados")
            btn_res.setObjectName("btnSecondary")
            btn_res.clicked.connect(lambda _, e_id=e["id"]: self.view_results(e_id))

            btn_edit = QPushButton("Editar")
            btn_edit.clicked.connect(lambda _, e_data=e: self.edit_exam(e_data))

            btn_del = QPushButton("Excluir")
            btn_del.setObjectName("btnDanger")
            btn_del.clicked.connect(lambda _, e_id=e["id"], e_nome=e["nome"]: self.delete_exam(e_id, e_nome))

            btn_layout.addWidget(btn_proc)
            btn_layout.addWidget(btn_res)
            btn_layout.addWidget(btn_edit)
            btn_layout.addWidget(btn_del)

            self.table.setCellWidget(row_idx, 6, btn_panel)

    def new_exam(self):
        dlg = ExamFormDialog(self.exam_model, self.subject_model, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Sucesso", "Prova cadastrada com sucesso!")
            self.load_exams()

    def edit_exam(self, exam_data):
        dlg = ExamFormDialog(self.exam_model, self.subject_model, self, exam_data=exam_data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Sucesso", "Prova atualizada com sucesso!")
            self.load_exams()

    def delete_exam(self, exam_id: int, exam_nome: str):
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja excluir a prova '{exam_nome}'? Todos os resultados associados também serão excluídos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.exam_model.delete_exam(exam_id)
                self.load_exams()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir prova: {str(e)}")

    def process_exam(self, exam_id: int):
        if self.on_process_request:
            self.on_process_request(exam_id)

    def view_results(self, exam_id: int):
        if self.on_view_results_request:
            self.on_view_results_request(exam_id)
