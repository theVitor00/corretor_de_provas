import qtawesome as qta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QDialog,
    QFormLayout, QMessageBox, QGroupBox, QSpinBox, QDoubleSpinBox,
    QDateEdit, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QDate
from models.exam import ExamModel
from models.subject import SubjectBlockModel

class AddPartDialog(QDialog):
    """
    Diálogo para cadastrar uma divisão / parte da prova (ex: Parte 1: Dia 1 - Humanas, Q1 a Q45)
    """
    def __init__(self, parte_num: int, start_q: int, parent=None):
        super().__init__(parent)
        self.parte_num = parte_num
        self.start_q = start_q
        self.setWindowTitle(f"Adicionar Divisão / Parte {parte_num}")
        self.setWindowIcon(qta.icon('fa5s.puzzle-piece', color='#242D64'))
        self.resize(360, 200)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.txt_nome = QLineEdit(f"Parte {self.parte_num}")
        self.spin_questoes = QSpinBox()
        self.spin_questoes.setRange(1, 200)
        self.spin_questoes.setValue(45)

        form.addRow("Nome da Parte / Etapa *:", self.txt_nome)
        form.addRow("Quantidade de Questões nesta Parte *:", self.spin_questoes)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setIcon(qta.icon('fa5s.times', color='#242D64'))
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)

        btn_add = QPushButton("Adicionar Parte")
        btn_add.setIcon(qta.icon('fa5s.plus', color='white'))
        btn_add.setObjectName("btnNavy")
        btn_add.clicked.connect(self.accept)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_add)
        layout.addLayout(btn_box)

    def get_data(self):
        num_q = self.spin_questoes.value()
        end_q = self.start_q + num_q - 1
        return {
            "parte_num": self.parte_num,
            "nome": self.txt_nome.text().strip(),
            "num_questoes": num_q,
            "q_start": self.start_q,
            "q_end": end_q
        }


class GabaritoMultiPartDialog(QDialog):
    """
    Diálogo para entrada de gabarito dividido pelas partes da prova
    """
    def __init__(self, tipo: str, partes: list, parent=None, existing_gabs: dict=None):
        super().__init__(parent)
        self.tipo = tipo
        self.partes = partes
        self.existing_gabs = existing_gabs or {}
        self.setWindowTitle(f"Cadastrar Gabarito para Tipo {tipo}")
        self.setWindowIcon(qta.icon('fa5s.key', color='#242D64'))
        self.resize(460, 260 + (len(partes) * 40))
        self.inputs = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        for p in self.partes:
            p_num = p["parte_num"]
            p_nome = p["nome"]
            q_st = p["q_start"]
            q_ed = p["q_end"]
            n_q = p["num_questoes"]

            txt = QLineEdit()
            txt.setPlaceholderText(f"Gabarito ({n_q} questões: ex: AAAAA...)")
            if str(p_num) in self.existing_gabs:
                txt.setText(self.existing_gabs[str(p_num)])
            elif p_num in self.existing_gabs:
                txt.setText(self.existing_gabs[p_num])

            form.addRow(f"<b>{p_nome}</b> (Q{q_st} a Q{q_ed}):", txt)
            self.inputs[p_num] = (txt, n_q)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setIcon(qta.icon('fa5s.times', color='#242D64'))
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Salvar Gabarito do Tipo")
        btn_save.setIcon(qta.icon('fa5s.check', color='white'))
        btn_save.setObjectName("btnNavy")
        btn_save.clicked.connect(self.validate_and_accept)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def validate_and_accept(self):
        for p_num, (txt, expected_len) in self.inputs.items():
            gab_str = txt.text().strip().upper()
            if not gab_str:
                QMessageBox.warning(self, "Aviso", f"Preencha o gabarito da Parte {p_num}.")
                return
            if len(gab_str) != expected_len:
                QMessageBox.warning(
                    self, "Aviso",
                    f"O gabarito da Parte {p_num} deve ter exatamente {expected_len} questões (informadas: {len(gab_str)})."
                )
                return
        self.accept()

    def get_data(self):
        partes_dict = {}
        unified = ""
        for p_num, (txt, _) in self.inputs.items():
            gab_str = txt.text().strip().upper()
            partes_dict[p_num] = gab_str
            unified += gab_str
        return partes_dict, unified


class SubjectRangeDialog(QDialog):
    def __init__(self, available_types: list, subjects_list: list, total_questions: int, partes: list=None, parent=None):
        super().__init__(parent)
        self.available_types = available_types
        self.subjects_list = subjects_list
        self.total_questions = total_questions
        self.partes = partes or []
        self.setWindowTitle("Adicionar Mapeamento de Disciplina por Tipo de Prova")
        self.setWindowIcon(qta.icon('fa5s.layer-group', color='#242D64'))
        self.resize(420, 260)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.combo_tipo = QComboBox()
        for t in self.available_types:
            self.combo_tipo.addItem(f"Tipo {t}", t)

        self.combo_parte = QComboBox()
        if self.partes:
            for p in self.partes:
                self.combo_parte.addItem(f"{p['nome']} (Q{p['q_start']} a Q{p['q_end']})", p)
            self.combo_parte.currentIndexChanged.connect(self.on_parte_changed)

        self.combo_subject = QComboBox()
        for s in self.subjects_list:
            self.combo_subject.addItem(s["nome"], s)

        self.spin_start = QSpinBox()
        self.spin_start.setRange(1, max(1, self.total_questions))

        self.spin_end = QSpinBox()
        self.spin_end.setRange(1, max(1, self.total_questions))

        if self.partes:
            p0 = self.partes[0]
            self.spin_start.setValue(p0["q_start"])
            self.spin_end.setValue(p0["q_end"])
        else:
            self.spin_start.setValue(1)
            self.spin_end.setValue(max(1, self.total_questions))

        form.addRow("Tipo da Prova *:", self.combo_tipo)
        if self.partes:
            form.addRow("Parte da Prova *:", self.combo_parte)
        form.addRow("Disciplina *:", self.combo_subject)
        form.addRow("Questão Inicial *:", self.spin_start)
        form.addRow("Questão Final *:", self.spin_end)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setIcon(qta.icon('fa5s.times', color='#242D64'))
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)

        btn_add = QPushButton("Adicionar")
        btn_add.setIcon(qta.icon('fa5s.plus', color='white'))
        btn_add.setObjectName("btnNavy")
        btn_add.clicked.connect(self.validate_and_accept)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_add)
        layout.addLayout(btn_box)

    def on_parte_changed(self):
        p = self.combo_parte.currentData()
        if p:
            self.spin_start.setValue(p["q_start"])
            self.spin_end.setValue(p["q_end"])

    def validate_and_accept(self):
        if self.spin_start.value() > self.spin_end.value():
            QMessageBox.warning(self, "Aviso", "A questão inicial não pode ser maior que a questão final.")
            return
        self.accept()

    def get_data(self):
        s_data = self.combo_subject.currentData()
        p_data = self.combo_parte.currentData() if self.partes else None
        return {
            "tipo": self.combo_tipo.currentData(),
            "parte_num": p_data["parte_num"] if p_data else 1,
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
        self.setWindowIcon(qta.icon('fa5s.file-signature', color='#242D64'))
        self.resize(800, 720)
        self.partes_list = [] # [{"parte_num": 1, "nome": "Parte 1", "num_questoes": 45, "q_start": 1, "q_end": 45}]
        self.gabaritos_map = {}  # {"1": "ABCDE...", "2": "..."}
        self.gabaritos_por_parte = {} # {"1": {1: "ABC...", 2: "DEF..."}}
        self.mapped_subjects = [] # [{"tipo": "1", "nome": "Matemática", "start_q": 1, "end_q": 10}]
        self.selected_blocos = [] # [{"id": 1, "nome": "Exatas"}]
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

        self.spin_valor = QDoubleSpinBox()
        self.spin_valor.setRange(1.0, 1000.0)
        self.spin_valor.setValue(10.0)
        self.spin_valor.setSingleStep(1.0)

        f_basic.addRow("Nome da Prova *:", self.txt_nome)
        f_basic.addRow("Data da Prova *:", self.txt_data)
        f_basic.addRow("Valor Total da Prova (Pontos):", self.spin_valor)
        layout.addWidget(gb_basic)

        # Divisões / Partes da Prova (Dias / Etapas estilo ENEM)
        gb_partes = QGroupBox("Divisões / Partes da Prova (Etapas/Dias)")
        l_partes = QVBoxLayout(gb_partes)

        h_p_controls = QHBoxLayout()
        btn_add_part = QPushButton("Adicionar Divisão / Parte")
        btn_add_part.setIcon(qta.icon('fa5s.plus', color='white'))
        btn_add_part.setObjectName("btnNavy")
        btn_add_part.clicked.connect(self.add_part)

        btn_rem_part = QPushButton("Remover Última Parte")
        btn_rem_part.setIcon(qta.icon('fa5s.trash-alt', color='#EF4444'))
        btn_rem_part.setObjectName("btnSecondary")
        btn_rem_part.clicked.connect(self.remove_last_part)

        h_p_controls.addWidget(btn_add_part)
        h_p_controls.addWidget(btn_rem_part)
        h_p_controls.addStretch()
        l_partes.addLayout(h_p_controls)

        self.list_partes = QListWidget()
        self.list_partes.setMaximumHeight(80)
        l_partes.addWidget(self.list_partes)
        layout.addWidget(gb_partes)

        # Blocos de Disciplinas
        gb_blocos = QGroupBox("Blocos de Disciplinas da Prova")
        l_blocos = QVBoxLayout(gb_blocos)

        h_b_controls = QHBoxLayout()
        self.combo_bloco = QComboBox()
        self.combo_bloco.addItem("Selecione um bloco para adicionar...", None)
        for b in self.subject_model.list_blocks():
            self.combo_bloco.addItem(b["nome"], b)

        btn_add_bloco = QPushButton("Adicionar Bloco")
        btn_add_bloco.setIcon(qta.icon('fa5s.plus', color='white'))
        btn_add_bloco.setObjectName("btnNavy")
        btn_add_bloco.clicked.connect(self.add_bloco_to_exam)

        btn_rem_bloco = QPushButton("Remover Bloco Selecionado")
        btn_rem_bloco.setIcon(qta.icon('fa5s.trash-alt', color='#EF4444'))
        btn_rem_bloco.setObjectName("btnSecondary")
        btn_rem_bloco.clicked.connect(self.remove_bloco_from_exam)

        h_b_controls.addWidget(self.combo_bloco, 1)
        h_b_controls.addWidget(btn_add_bloco)
        h_b_controls.addWidget(btn_rem_bloco)
        l_blocos.addLayout(h_b_controls)

        self.list_blocos = QListWidget()
        self.list_blocos.setMaximumHeight(75)
        l_blocos.addWidget(self.list_blocos)

        layout.addWidget(gb_blocos)

        # Tipos e Gabaritos
        gb_gab = QGroupBox("Tipos de Prova e Gabaritos")
        l_gab = QVBoxLayout(gb_gab)

        h_g_controls = QHBoxLayout()
        self.txt_tipo = QLineEdit()
        self.txt_tipo.setPlaceholderText("Tipo (ex: 1, 2, A, B)")
        self.txt_tipo.setMaximumWidth(120)

        btn_add_gab = QPushButton("Adicionar / Editar Gabarito por Tipo")
        btn_add_gab.setIcon(qta.icon('fa5s.key', color='white'))
        btn_add_gab.setObjectName("btnNavy")
        btn_add_gab.clicked.connect(self.add_gabarito)

        h_g_controls.addWidget(QLabel("Tipo:"))
        h_g_controls.addWidget(self.txt_tipo)
        h_g_controls.addWidget(btn_add_gab)
        h_g_controls.addStretch()
        l_gab.addLayout(h_g_controls)

        self.tbl_gabaritos = QTableWidget()
        self.tbl_gabaritos.setColumnCount(3)
        self.tbl_gabaritos.setHorizontalHeaderLabels(["Tipo", "Respostas do Gabarito (Completo)", "Ação"])
        self.tbl_gabaritos.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_gabaritos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_gabaritos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        l_gab.addWidget(self.tbl_gabaritos)

        layout.addWidget(gb_gab)

        # Mapeamento por Disciplinas e Tipo
        gb_map = QGroupBox("Mapeamento Posicional por Disciplina, Tipo e Parte")
        l_map = QVBoxLayout(gb_map)

        h_m_controls = QHBoxLayout()
        btn_add_map = QPushButton("Definir Faixa por Disciplina e Tipo")
        btn_add_map.setIcon(qta.icon('fa5s.layer-group', color='#242D64'))
        btn_add_map.setObjectName("btnSecondary")
        btn_add_map.clicked.connect(self.add_subject_mapping)

        btn_rem_map = QPushButton("Remover Mapeamento Selecionado")
        btn_rem_map.setIcon(qta.icon('fa5s.trash-alt', color='#EF4444'))
        btn_rem_map.setObjectName("btnSecondary")
        btn_rem_map.clicked.connect(self.remove_subject_mapping)

        h_m_controls.addWidget(btn_add_map)
        h_m_controls.addWidget(btn_rem_map)
        h_m_controls.addStretch()
        l_map.addLayout(h_m_controls)

        self.list_map = QListWidget()
        self.list_map.setMaximumHeight(85)
        l_map.addWidget(self.list_map)

        layout.addWidget(gb_map)

        # Populate if editing
        if self.exam_data:
            self.txt_nome.setText(self.exam_data["nome"])
            q_date = QDate.fromString(self.exam_data["data"], "yyyy-MM-dd")
            if q_date.isValid():
                self.txt_data.setDate(q_date)

            self.spin_valor.setValue(float(self.exam_data.get("valor_total", 10.0)))
            self.gabaritos_map = self.exam_data.get("gabaritos", {})
            cfg = self.exam_data.get("layout_config", {})
            self.partes_list = cfg.get("partes", [])
            self.gabaritos_por_parte = cfg.get("gabaritos_por_parte", {})
            self.mapped_subjects = cfg.get("subjects", [])
            self.selected_blocos = self.exam_data.get("blocos_list", [])

            self.refresh_partes_list()
            self.refresh_blocos_list()
            self.refresh_gabaritos_table()
            self.refresh_mapped_subjects_list()

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setIcon(qta.icon('fa5s.times', color='#242D64'))
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Salvar Prova")
        btn_save.setIcon(qta.icon('fa5s.save', color='white'))
        btn_save.setObjectName("btnNavy")
        btn_save.clicked.connect(self.validate_and_save)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def add_part(self):
        p_num = len(self.partes_list) + 1
        start_q = 1 if not self.partes_list else self.partes_list[-1]["q_end"] + 1
        dlg = AddPartDialog(p_num, start_q, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            p_data = dlg.get_data()
            self.partes_list.append(p_data)
            self.refresh_partes_list()

    def remove_last_part(self):
        if self.partes_list:
            self.partes_list.pop()
            self.refresh_partes_list()

    def refresh_partes_list(self):
        self.list_partes.clear()
        if not self.partes_list:
            self.list_partes.addItem("• Nenhuma divisão adicionada (Prova em Parte Única).")
        else:
            for p in self.partes_list:
                self.list_partes.addItem(f"• Parte {p['parte_num']}: {p['nome']} (Questão {p['q_start']} a {p['q_end']} - {p['num_questoes']} Qs)")

    def get_effective_partes(self):
        if self.partes_list:
            return self.partes_list
        # Se não adicionou nenhuma parte, assumir 1 parte padrão
        total_q = 45
        if self.gabaritos_map:
            total_q = len(next(iter(self.gabaritos_map.values())))
        return [{
            "parte_num": 1,
            "nome": "Parte Única",
            "num_questoes": total_q,
            "q_start": 1,
            "q_end": total_q
        }]

    def add_bloco_to_exam(self):
        bloco = self.combo_bloco.currentData()
        if not bloco:
            QMessageBox.warning(self, "Aviso", "Selecione um bloco de disciplinas válido.")
            return

        if any(b["id"] == bloco["id"] for b in self.selected_blocos):
            QMessageBox.warning(self, "Bloco Redundante", f"O bloco '{bloco['nome']}' já foi adicionado a esta prova.")
            return

        self.selected_blocos.append(bloco)
        self.refresh_blocos_list()

    def remove_bloco_from_exam(self):
        row = self.list_blocos.currentRow()
        if row >= 0 and row < len(self.selected_blocos):
            del self.selected_blocos[row]
            self.refresh_blocos_list()

    def refresh_blocos_list(self):
        self.list_blocos.clear()
        for b in self.selected_blocos:
            self.list_blocos.addItem(f"• Bloco: {b['nome']}")

    def add_gabarito(self):
        tipo = self.txt_tipo.text().strip()
        if not tipo:
            QMessageBox.warning(self, "Aviso", "Informe o Tipo da Prova (ex: 1, 2, A, B).")
            return

        partes = self.get_effective_partes()
        existing_p_gabs = self.gabaritos_por_parte.get(tipo, {})
        dlg = GabaritoMultiPartDialog(tipo, partes, self, existing_p_gabs)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            p_dict, unified_str = dlg.get_data()
            self.gabaritos_por_parte[tipo] = p_dict
            self.gabaritos_map[tipo] = unified_str
            self.txt_tipo.clear()
            self.refresh_gabaritos_table()

    def remove_gabarito(self, tipo: str):
        if tipo in self.gabaritos_map:
            del self.gabaritos_map[tipo]
        if tipo in self.gabaritos_por_parte:
            del self.gabaritos_por_parte[tipo]
        self.refresh_gabaritos_table()

    def refresh_gabaritos_table(self):
        self.tbl_gabaritos.setRowCount(len(self.gabaritos_map))
        for row_idx, (tipo, gab) in enumerate(self.gabaritos_map.items()):
            self.tbl_gabaritos.setItem(row_idx, 0, QTableWidgetItem(tipo))
            self.tbl_gabaritos.setItem(row_idx, 1, QTableWidgetItem(f"{gab} ({len(gab)} Qs)"))

            btn_del = QPushButton("Remover")
            btn_del.setIcon(qta.icon('fa5s.trash-alt', color='white'))
            btn_del.setObjectName("btnDanger")
            btn_del.clicked.connect(lambda _, t=tipo: self.remove_gabarito(t))
            self.tbl_gabaritos.setCellWidget(row_idx, 2, btn_del)

    def add_subject_mapping(self):
        if not self.gabaritos_map:
            QMessageBox.warning(self, "Aviso", "Cadastre ao menos um tipo de gabarito antes de mapear disciplinas.")
            return

        available_types = list(self.gabaritos_map.keys())
        num_q = len(next(iter(self.gabaritos_map.values())))
        all_subjects = self.subject_model.list_subjects()
        if not all_subjects:
            QMessageBox.warning(self, "Aviso", "Nenhuma disciplina cadastrada no sistema. Cadastre disciplinas na aba 'Disciplinas e Blocos'.")
            return

        partes = self.get_effective_partes()
        dlg = SubjectRangeDialog(available_types, all_subjects, num_q, partes, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            self.mapped_subjects.append(data)
            self.refresh_mapped_subjects_list()

    def remove_subject_mapping(self):
        row = self.list_map.currentRow()
        if row >= 0 and row < len(self.mapped_subjects):
            del self.mapped_subjects[row]
            self.refresh_mapped_subjects_list()

    def refresh_mapped_subjects_list(self):
        self.list_map.clear()
        for idx, m in enumerate(self.mapped_subjects):
            tipo_label = f"Tipo {m.get('tipo')}" if m.get('tipo') else "Todos"
            text = f"• [{tipo_label}] {m['nome']}: Questão {m['start_q']} até Questão {m['end_q']}"
            item = QListWidgetItem(text)
            self.list_map.addItem(item)

    def validate_and_save(self):
        nome = self.txt_nome.text().strip()
        data = self.txt_data.date().toString("yyyy-MM-dd")
        valor_total = self.spin_valor.value()
        bloco_ids = [b["id"] for b in self.selected_blocos]

        if not nome or not data:
            QMessageBox.warning(self, "Campos Obrigatórios", "Informe o Nome e a Data da prova.")
            return

        if not self.gabaritos_map:
            QMessageBox.warning(self, "Gabarito Obrigatório", "A prova precisa ter ao menos um tipo de gabarito cadastrado.")
            return

        partes = self.get_effective_partes()
        layout_config = {
            "partes": partes,
            "gabaritos_por_parte": self.gabaritos_por_parte,
            "subjects": self.mapped_subjects
        }

        try:
            if self.exam_data:
                self.exam_model.update_exam(
                    self.exam_data["id"], nome, data, self.gabaritos_map,
                    bloco_ids=bloco_ids, valor_total=valor_total, layout_config=layout_config
                )
            else:
                self.exam_model.create_exam(
                    nome, data, self.gabaritos_map,
                    bloco_ids=bloco_ids, valor_total=valor_total, layout_config=layout_config
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar Prova", str(e))


from services.abbreviations import get_acronym

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
        btn_new_exam = QPushButton("Cadastrar Nova Prova")
        btn_new_exam.setIcon(qta.icon('fa5s.plus', color='white'))
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
            "ID", "Data", "Nome da Prova", "Bloco(s)", "Tipos de Gabarito", "Total Alunos", "Ações"
        ])
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 440)

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
            full_b_name = str(e.get("bloco_nome") or "-")
            if full_b_name and full_b_name != "-":
                b_parts = [p.strip() for p in full_b_name.split(",") if p.strip()]
                siglas_str = ", ".join(get_acronym(p) for p in b_parts)
            else:
                siglas_str = "-"

            item_bloco = QTableWidgetItem(siglas_str)
            item_bloco.setToolTip(f"Bloco(s): {full_b_name}")
            self.table.setItem(row_idx, 3, item_bloco)
            
            tipos_str = ", ".join(e.get("gabaritos", {}).keys())
            self.table.setItem(row_idx, 4, QTableWidgetItem(tipos_str))
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(e.get("total_processados", 0))))

            btn_panel = QWidget()
            btn_layout = QHBoxLayout(btn_panel)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(6)

            btn_proc = QPushButton("Processar")
            btn_proc.setIcon(qta.icon('fa5s.cogs', color='white'))
            btn_proc.setObjectName("btnNavy")
            btn_proc.setMinimumWidth(100)
            btn_proc.clicked.connect(lambda _, e_id=e["id"]: self.process_exam(e_id))

            btn_res = QPushButton("Resultados")
            btn_res.setIcon(qta.icon('fa5s.chart-line', color='#242D64'))
            btn_res.setObjectName("btnSecondary")
            btn_res.setMinimumWidth(105)
            btn_res.clicked.connect(lambda _, e_id=e["id"]: self.view_results(e_id))

            btn_edit = QPushButton("Editar")
            btn_edit.setIcon(qta.icon('fa5s.edit', color='#242D64'))
            btn_edit.setObjectName("btnSecondary")
            btn_edit.setMinimumWidth(85)
            btn_edit.clicked.connect(lambda _, e_data=e: self.edit_exam(e_data))

            btn_del = QPushButton("Excluir")
            btn_del.setIcon(qta.icon('fa5s.trash-alt', color='white'))
            btn_del.setObjectName("btnDanger")
            btn_del.setMinimumWidth(85)
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
        # Buscar dados completos incluindo blocos_list
        full_exam = self.exam_model.get_exam_by_id(exam_data["id"])
        dlg = ExamFormDialog(self.exam_model, self.subject_model, self, exam_data=full_exam)
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
