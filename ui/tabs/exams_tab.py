import qtawesome as qta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QDialog,
    QFormLayout, QMessageBox, QGroupBox, QSpinBox, QDoubleSpinBox,
    QDateEdit, QListWidget, QListWidgetItem, QRadioButton, QButtonGroup,
    QScrollArea, QFrame, QCheckBox
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
        self.resize(380, 220)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
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


class GabaritoTableDialog(QDialog):
    """
    Diálogo para exibição e edição estruturada do gabarito em tabela por questão.
    Exibe alternativas e permite anular questões com aviso de reprocessamento.
    """
    def __init__(self, modelo: str, partes: list, mapped_subjects: list = None, parent=None, existing_gabs: dict = None, existing_unified: str = ""):
        super().__init__(parent)
        self.modelo = modelo
        self.partes = partes or []
        self.mapped_subjects = mapped_subjects or []
        self.existing_gabs = existing_gabs or {}
        self.existing_unified = existing_unified or ""
        self.has_shown_popup = False
        self.result_partes_dict = {}
        self.result_unified_str = ""

        self.setWindowTitle(f"Editar Gabarito em Tabela - Modelo {modelo}")
        self.setWindowIcon(qta.icon('fa5s.table', color='#242D64'))
        self.resize(780, 560)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Barra superior com entrada em texto rápido
        gb_quick = QGroupBox("Importar / Colar Sequência de Respostas")
        h_quick = QHBoxLayout(gb_quick)

        self.txt_quick = QLineEdit()
        self.txt_quick.setPlaceholderText("Cole a sequência de respostas (ex: ABCD*ABCDE...)")
        
        initial_str = self.existing_unified
        if not initial_str and self.partes:
            full_str = ""
            for p in self.partes:
                p_num = p["parte_num"]
                full_str += str(self.existing_gabs.get(str(p_num)) or self.existing_gabs.get(p_num) or ("A" * p["num_questoes"]))
            initial_str = full_str

        self.txt_quick.setText(initial_str)

        btn_apply_quick = QPushButton("Aplicar Sequência")
        btn_apply_quick.setIcon(qta.icon('fa5s.magic', color='#242D64'))
        btn_apply_quick.setObjectName("btnSecondary")
        btn_apply_quick.clicked.connect(self.apply_quick_string)

        h_quick.addWidget(QLabel("Gabarito Rápido:"))
        h_quick.addWidget(self.txt_quick, 1)
        h_quick.addWidget(btn_apply_quick)
        layout.addWidget(gb_quick)

        # Tabela principal de gabarito por questão
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(5)
        self.tbl.setHorizontalHeaderLabels(["Questão #", "Parte / Divisão", "Disciplina", "Gabarito (Alternativa)", "Anulação"])
        self.tbl.verticalHeader().setDefaultSectionSize(36)
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.tbl)

        # Rodapé com estatísticas e botões de ação
        h_footer = QHBoxLayout()
        self.lbl_stats = QLabel("Total: 0 Qs | Ativas: 0 | Anuladas: 0")
        self.lbl_stats.setStyleSheet("font-weight: bold; color: #242D64; font-size: 13px;")

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setIcon(qta.icon('fa5s.times', color='#242D64'))
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Salvar Gabarito do Modelo")
        btn_save.setIcon(qta.icon('fa5s.check', color='white'))
        btn_save.setObjectName("btnNavy")
        btn_save.clicked.connect(self.validate_and_accept)

        h_footer.addWidget(self.lbl_stats)
        h_footer.addStretch()
        h_footer.addWidget(btn_cancel)
        h_footer.addWidget(btn_save)
        layout.addLayout(h_footer)

        self.populate_table(initial_str)

    def populate_table(self, gab_str: str):
        total_q = sum(p["num_questoes"] for p in self.partes) if self.partes else len(gab_str or "A"*45)
        if not self.partes:
            self.partes = [{"parte_num": 1, "nome": "Parte Única", "num_questoes": total_q, "q_start": 1, "q_end": total_q}]

        gab_str = (gab_str or "").upper().ljust(total_q, "A")[:total_q]
        self.tbl.setRowCount(total_q)

        for p in self.partes:
            p_num = p["parte_num"]
            p_nome = f"Parte {p_num}: {p['nome']}"
            q_st = p["q_start"]
            q_ed = p["q_end"]

            for q_idx in range(q_st, q_ed + 1):
                row_i = q_idx - 1
                curr_char = gab_str[row_i] if row_i < len(gab_str) else "A"

                item_q = QTableWidgetItem(f"Q{q_idx:02d}" if total_q >= 10 else f"Q{q_idx}")
                item_q.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_q.setFlags(item_q.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tbl.setItem(row_i, 0, item_q)

                item_p = QTableWidgetItem(p_nome)
                item_p.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_p.setFlags(item_p.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tbl.setItem(row_i, 1, item_p)

                d_name = "Geral"
                for m in self.mapped_subjects:
                    m_mod = str(m.get("modelo") or m.get("tipo") or "")
                    if not m_mod or m_mod.lower() == str(self.modelo).lower():
                        if m["start_q"] <= q_idx <= m["end_q"]:
                            d_name = m["nome"]
                            break
                item_d = QTableWidgetItem(d_name)
                item_d.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_d.setFlags(item_d.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tbl.setItem(row_i, 2, item_d)

                combo = QComboBox()
                combo.addItems(["A", "B", "C", "D", "E", "* (ANULADA)"])
                is_annulled = (curr_char in ["*", "X", "ANULADA"])
                if is_annulled:
                    combo.setCurrentIndex(5)
                elif curr_char in ["A", "B", "C", "D", "E"]:
                    combo.setCurrentText(curr_char)
                else:
                    combo.setCurrentIndex(0)

                chk = QCheckBox("Anular Questão")
                chk.setChecked(is_annulled)

                combo.currentIndexChanged.connect(lambda _, r=row_i: self.on_combo_changed(r))
                chk.toggled.connect(lambda checked, r=row_i: self.on_chk_toggled(r, checked))

                self.tbl.setCellWidget(row_i, 3, combo)
                self.tbl.setCellWidget(row_i, 4, chk)

        self.update_stats()

    def on_combo_changed(self, row: int):
        combo = self.tbl.cellWidget(row, 3)
        chk = self.tbl.cellWidget(row, 4)
        if not combo or not chk:
            return

        is_annulled = (combo.currentIndex() == 5)
        chk.blockSignals(True)
        chk.setChecked(is_annulled)
        chk.blockSignals(False)

        if is_annulled:
            self.notify_annulment(row + 1)
        self.update_stats()

    def on_chk_toggled(self, row: int, checked: bool):
        combo = self.tbl.cellWidget(row, 3)
        chk = self.tbl.cellWidget(row, 4)
        if not combo or not chk:
            return

        combo.blockSignals(True)
        if checked:
            combo.setCurrentIndex(5)
            combo.blockSignals(False)
            self.notify_annulment(row + 1)
        else:
            if combo.currentIndex() == 5:
                combo.setCurrentIndex(0)
            combo.blockSignals(False)
        self.update_stats()

    def notify_annulment(self, q_num: int):
        if not self.has_shown_popup:
            self.has_shown_popup = True
            QMessageBox.information(
                self,
                "Questão Anulada",
                f"A <b>Questão {q_num}</b> foi marcada como <b>ANULADA</b>.<br><br>"
                "Os pesos das questões ativas desta disciplina serão redistribuídos automaticamente para manter a pontuação total da prova.<br><br>"
                "⚠️ <b>Atenção: É necessário reprocessar as respostas dos alunos na aba 'Processamento de Provas' para recalcular boletins e notas.</b>"
            )

    def apply_quick_string(self):
        new_str = self.txt_quick.text().strip().upper()
        if new_str:
            self.populate_table(new_str)

    def update_stats(self):
        total_q = self.tbl.rowCount()
        annulled_q = 0
        for r in range(total_q):
            chk = self.tbl.cellWidget(r, 4)
            if chk and chk.isChecked():
                annulled_q += 1
        active_q = total_q - annulled_q
        self.lbl_stats.setText(f"Total: {total_q} Qs &nbsp;|&nbsp; <font color='#16A34A'>Ativas: {active_q}</font> &nbsp;|&nbsp; <font color='#DC2626'>Anuladas: {annulled_q}</font>")

    def validate_and_accept(self):
        partes_dict = {}
        unified_list = []

        q_idx = 0
        for p in self.partes:
            p_num = p["parte_num"]
            p_str = ""
            for _ in range(p["num_questoes"]):
                combo = self.tbl.cellWidget(q_idx, 3)
                chk = self.tbl.cellWidget(q_idx, 4)
                if chk and chk.isChecked():
                    char = "*"
                elif combo:
                    c_txt = combo.currentText()
                    char = c_txt[0] if c_txt else "A"
                else:
                    char = "A"
                p_str += char
                unified_list.append(char)
                q_idx += 1
            partes_dict[p_num] = p_str

        self.result_partes_dict = partes_dict
        self.result_unified_str = "".join(unified_list)
        self.accept()

    def get_data(self):
        return self.result_partes_dict, self.result_unified_str


class GabaritoMultiPartDialog(GabaritoTableDialog):
    """
    Alias retrocompatível que utiliza a tabela interativa para gerenciar gabaritos.
    """
    pass


class SubjectRangeDialog(QDialog):
    def __init__(self, available_models: list, subjects_list: list, total_questions: int, partes: list=None, parent=None):
        super().__init__(parent)
        self.available_models = available_models
        self.subjects_list = subjects_list
        self.total_questions = total_questions
        self.partes = partes or []
        self.setWindowTitle("Adicionar Mapeamento de Disciplina por Modelo de Prova")
        self.setWindowIcon(qta.icon('fa5s.layer-group', color='#242D64'))
        self.resize(460, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        form = QFormLayout()

        self.combo_modelo = QComboBox()
        for m in self.available_models:
            self.combo_modelo.addItem(f"Modelo {m}", m)

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

        self.spin_peso = QDoubleSpinBox()
        self.spin_peso.setRange(0.0001, 100.0)
        self.spin_peso.setValue(1.0)
        self.spin_peso.setSingleStep(0.0001)
        self.spin_peso.setDecimals(4)

        if self.partes:
            p0 = self.partes[0]
            self.spin_start.setValue(p0["q_start"])
            self.spin_end.setValue(p0["q_end"])
        else:
            self.spin_start.setValue(1)
            self.spin_end.setValue(max(1, self.total_questions))

        form.addRow("Modelo da Prova *:", self.combo_modelo)
        if self.partes:
            form.addRow("Parte da Prova *:", self.combo_parte)
        form.addRow("Disciplina *:", self.combo_subject)
        form.addRow("Questão Inicial *:", self.spin_start)
        form.addRow("Questão Final *:", self.spin_end)
        form.addRow("Peso por Questão *:", self.spin_peso)

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
        if self.spin_peso.value() <= 0:
            QMessageBox.warning(self, "Aviso", "O peso da questão é obrigatório e deve ser maior que zero.")
            return
        self.accept()

    def get_data(self):
        s_data = self.combo_subject.currentData()
        p_data = self.combo_parte.currentData() if self.partes else None
        mod_val = self.combo_modelo.currentData()
        return {
            "modelo": mod_val,
            "tipo": mod_val, # compatibilidade
            "parte_num": p_data["parte_num"] if p_data else 1,
            "subject_id": s_data["id"],
            "nome": s_data["nome"],
            "start_q": self.spin_start.value(),
            "end_q": self.spin_end.value(),
            "peso": float(self.spin_peso.value())
        }


class ExamFormDialog(QDialog):
    def __init__(self, exam_model: ExamModel, subject_model: SubjectBlockModel, parent=None, exam_data=None):
        super().__init__(parent)
        self.exam_model = exam_model
        self.subject_model = subject_model
        self.exam_data = exam_data
        self.setWindowTitle("Editar Prova" if exam_data else "Nova Prova")
        self.setWindowIcon(qta.icon('fa5s.file-signature', color='#242D64'))
        self.resize(1150, 720)
        self.setMinimumSize(950, 580)
        self.partes_list = []
        self.gabaritos_map = {}  # {"1": "ABCDE...", "2": "..."}
        self.gabaritos_por_parte = {}
        self.mapped_subjects = []
        self.selected_blocos = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Scroll Area para garantir ajuste dinâmico em telas pequenas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        h_columns = QHBoxLayout(content_widget)
        h_columns.setContentsMargins(6, 6, 6, 6)
        h_columns.setSpacing(14)

        # Coluna da Esquerda (Dados Básicos, Partes, Blocos)
        v_col_left = QVBoxLayout()

        # Dados Básicos
        gb_basic = QGroupBox("Dados Básicos da Prova")
        f_basic = QFormLayout(gb_basic)

        self.txt_nome = QLineEdit()
        self.txt_data = QDateEdit()
        self.txt_data.setDate(QDate.currentDate())
        self.txt_data.setCalendarPopup(True)

        self.combo_tipo_prova = QComboBox()
        self.combo_tipo_prova.addItems([
            "Prova Regular",
            "Simulado",
            "Prova de Seleção",
            "Atividade de Rotina"
        ])

        self.combo_trimestre = QComboBox()
        self.combo_trimestre.addItems([
            "1º Trimestre",
            "2º Trimestre",
            "3º Trimestre"
        ])

        self.spin_valor = QDoubleSpinBox()
        self.spin_valor.setRange(1.0, 1000.0)
        self.spin_valor.setValue(10.0)
        self.spin_valor.setSingleStep(1.0)

        # Radio buttons para Redação (Sim / Não)
        h_redacao = QHBoxLayout()
        self.rb_redacao_sim = QRadioButton("Sim")
        self.rb_redacao_nao = QRadioButton("Não")
        self.rb_redacao_nao.setChecked(True)
        self.bg_redacao = QButtonGroup(self)
        self.bg_redacao.addButton(self.rb_redacao_sim)
        self.bg_redacao.addButton(self.rb_redacao_nao)
        h_redacao.addWidget(self.rb_redacao_sim)
        h_redacao.addWidget(self.rb_redacao_nao)
        h_redacao.addStretch()

        f_basic.addRow("Nome da Prova *:", self.txt_nome)
        f_basic.addRow("Data da Prova *:", self.txt_data)
        f_basic.addRow("Tipo de Prova *:", self.combo_tipo_prova)
        f_basic.addRow("Trimestre *:", self.combo_trimestre)
        f_basic.addRow("Valor Total da Prova (Pontos):", self.spin_valor)
        f_basic.addRow("Possui Redação? *:", h_redacao)
        v_col_left.addWidget(gb_basic)

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
        self.list_partes.setMaximumHeight(85)
        l_partes.addWidget(self.list_partes)
        v_col_left.addWidget(gb_partes)

        # Blocos de Disciplinas
        gb_blocos = QGroupBox("Blocos de Disciplinas da Prova (Opcional)")
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
        self.list_blocos.setMaximumHeight(80)
        l_blocos.addWidget(self.list_blocos)
        v_col_left.addWidget(gb_blocos)
        v_col_left.addStretch()

        # Coluna da Direita (Modelos e Gabaritos, Mapeamento)
        v_col_right = QVBoxLayout()

        # Modelos e Gabaritos
        gb_gab = QGroupBox("Modelos de Prova e Gabaritos")
        l_gab = QVBoxLayout(gb_gab)

        h_g_controls = QHBoxLayout()
        self.txt_modelo = QLineEdit()
        self.txt_modelo.setPlaceholderText("Modelo (ex: 1, 2, A, B)")
        self.txt_modelo.setMaximumWidth(130)

        btn_add_gab = QPushButton("Adicionar / Editar Gabarito por Modelo")
        btn_add_gab.setIcon(qta.icon('fa5s.key', color='white'))
        btn_add_gab.setObjectName("btnNavy")
        btn_add_gab.clicked.connect(self.add_gabarito)

        h_g_controls.addWidget(QLabel("Modelo:"))
        h_g_controls.addWidget(self.txt_modelo)
        h_g_controls.addWidget(btn_add_gab)
        h_g_controls.addStretch()
        l_gab.addLayout(h_g_controls)

        self.tbl_gabaritos = QTableWidget()
        self.tbl_gabaritos.setColumnCount(3)
        self.tbl_gabaritos.setHorizontalHeaderLabels(["Modelo", "Respostas do Gabarito (Completo)", "Ação"])
        self.tbl_gabaritos.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_gabaritos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_gabaritos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_gabaritos.setMaximumHeight(130)
        l_gab.addWidget(self.tbl_gabaritos)
        v_col_right.addWidget(gb_gab)

        # Mapeamento por Disciplinas e Modelo
        gb_map = QGroupBox("Mapeamento Posicional por Disciplina, Modelo e Parte")
        l_map = QVBoxLayout(gb_map)

        h_m_controls = QHBoxLayout()
        btn_add_map = QPushButton("Definir Faixa por Disciplina e Modelo")
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
        self.list_map.setMaximumHeight(110)
        l_map.addWidget(self.list_map)
        v_col_right.addWidget(gb_map)
        v_col_right.addStretch()

        h_columns.addLayout(v_col_left, 1)
        h_columns.addLayout(v_col_right, 1)

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

        # Populate if editing
        if self.exam_data:
            self.txt_nome.setText(self.exam_data["nome"])
            q_date = QDate.fromString(self.exam_data["data"], "yyyy-MM-dd")
            if q_date.isValid():
                self.txt_data.setDate(q_date)

            t_prova = self.exam_data.get("tipo_prova", "Prova Regular")
            idx_tp = self.combo_tipo_prova.findText(t_prova)
            if idx_tp >= 0:
                self.combo_tipo_prova.setCurrentIndex(idx_tp)

            trim = self.exam_data.get("trimestre", "1º Trimestre")
            idx_tr = self.combo_trimestre.findText(trim)
            if idx_tr >= 0:
                self.combo_trimestre.setCurrentIndex(idx_tr)

            self.spin_valor.setValue(float(self.exam_data.get("valor_total", 10.0)))
            if self.exam_data.get("possui_redacao"):
                self.rb_redacao_sim.setChecked(True)
            else:
                self.rb_redacao_nao.setChecked(True)

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
        modelo = self.txt_modelo.text().strip()
        if not modelo:
            QMessageBox.warning(self, "Aviso", "Informe o Modelo da Prova (ex: 1, 2, A, B).")
            return

        partes = self.get_effective_partes()
        existing_p_gabs = self.gabaritos_por_parte.get(modelo, {})
        existing_unified = self.gabaritos_map.get(modelo, "")

        dlg = GabaritoTableDialog(modelo, partes, self.mapped_subjects, self, existing_p_gabs, existing_unified)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            p_dict, unified_str = dlg.get_data()
            self.gabaritos_por_parte[modelo] = p_dict
            self.gabaritos_map[modelo] = unified_str
            self.txt_modelo.clear()
            self.refresh_gabaritos_table()

    def edit_gabarito_model(self, modelo: str):
        self.txt_modelo.setText(modelo)
        self.add_gabarito()

    def remove_gabarito(self, modelo: str):
        if modelo in self.gabaritos_map:
            del self.gabaritos_map[modelo]
        if modelo in self.gabaritos_por_parte:
            del self.gabaritos_por_parte[modelo]
        self.refresh_gabaritos_table()

    def refresh_gabaritos_table(self):
        self.tbl_gabaritos.setRowCount(len(self.gabaritos_map))
        for row_idx, (mod, gab) in enumerate(self.gabaritos_map.items()):
            self.tbl_gabaritos.setItem(row_idx, 0, QTableWidgetItem(mod))

            annulled_cnt = gab.count("*") + gab.count("X")
            info_str = f"{gab} ({len(gab)} Qs)"
            if annulled_cnt > 0:
                info_str += f" — ⚠️ {annulled_cnt} Anulada(s)"

            self.tbl_gabaritos.setItem(row_idx, 1, QTableWidgetItem(info_str))

            w_actions = QWidget()
            h_act = QHBoxLayout(w_actions)
            h_act.setContentsMargins(2, 2, 2, 2)
            h_act.setSpacing(4)

            btn_edit = QPushButton("Editar Tabela")
            btn_edit.setIcon(qta.icon('fa5s.table', color='#242D64'))
            btn_edit.setObjectName("btnSecondary")
            btn_edit.clicked.connect(lambda _, m=mod: self.edit_gabarito_model(m))

            btn_del = QPushButton("Remover")
            btn_del.setIcon(qta.icon('fa5s.trash-alt', color='white'))
            btn_del.setObjectName("btnDanger")
            btn_del.clicked.connect(lambda _, m=mod: self.remove_gabarito(m))

            h_act.addWidget(btn_edit)
            h_act.addWidget(btn_del)
            self.tbl_gabaritos.setCellWidget(row_idx, 2, w_actions)

    def add_subject_mapping(self):
        if not self.gabaritos_map:
            QMessageBox.warning(self, "Aviso", "Cadastre ao menos um modelo de gabarito antes de mapear disciplinas.")
            return

        available_models = list(self.gabaritos_map.keys())
        num_q = len(next(iter(self.gabaritos_map.values())))
        all_subjects = self.subject_model.list_subjects()
        if not all_subjects:
            QMessageBox.warning(self, "Aviso", "Nenhuma disciplina cadastrada no sistema. Cadastre disciplinas na aba 'Disciplinas e Blocos'.")
            return

        partes = self.get_effective_partes()
        dlg = SubjectRangeDialog(available_models, all_subjects, num_q, partes, self)
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
            mod_val = m.get('modelo') or m.get('tipo')
            mod_label = f"Modelo {mod_val}" if mod_val else "Todos"
            peso_val = m.get('peso', 1.0)
            text = f"• [{mod_label}] {m['nome']}: Questão {m['start_q']} a {m['end_q']} (Peso: {peso_val})"
            item = QListWidgetItem(text)
            self.list_map.addItem(item)

    def validate_and_save(self):
        nome = self.txt_nome.text().strip()
        data = self.txt_data.date().toString("yyyy-MM-dd")
        tipo_prova = self.combo_tipo_prova.currentText()
        trimestre = self.combo_trimestre.currentText()
        valor_total = self.spin_valor.value()
        possui_redacao = self.rb_redacao_sim.isChecked()
        bloco_ids = [b["id"] for b in self.selected_blocos]

        if not nome or not data:
            QMessageBox.warning(self, "Campos Obrigatórios", "Informe o Nome e a Data da prova.")
            return

        if not self.gabaritos_map:
            QMessageBox.warning(self, "Gabarito Obrigatório", "A prova precisa ter ao menos um modelo de gabarito cadastrado.")
            return

        partes = self.get_effective_partes()
        layout_config = {
            "partes": partes,
            "gabaritos_por_parte": self.gabaritos_por_parte,
            "subjects": self.mapped_subjects
        }

        has_annulled = any("*" in g or "X" in g for g in self.gabaritos_map.values())

        try:
            if self.exam_data:
                self.exam_model.update_exam(
                    self.exam_data["id"], nome, data, self.gabaritos_map,
                    bloco_ids=bloco_ids, valor_total=valor_total, possui_redacao=possui_redacao,
                    tipo_prova=tipo_prova, trimestre=trimestre, layout_config=layout_config
                )
            else:
                self.exam_model.create_exam(
                    nome, data, self.gabaritos_map,
                    bloco_ids=bloco_ids, valor_total=valor_total, possui_redacao=possui_redacao,
                    tipo_prova=tipo_prova, trimestre=trimestre, layout_config=layout_config
                )
            if has_annulled:
                QMessageBox.information(
                    self,
                    "Reprocessamento Necessário",
                    "A prova contém questões **anuladas** (*).\n\n"
                    "Para que a redistribuição dos pesos e novos boletins sejam aplicados às notas dos alunos, vá para a aba **Processamento de Provas** e execute o reprocessamento."
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
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

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
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Data", "Trimestre", "Tipo de Prova", "Nome da Prova", "Bloco(s)", "Modelos de Gabarito", "Redação", "Total Alunos", "Ações"
        ])
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(9, 530)

        l_hist.addWidget(self.table)
        layout.addWidget(gb_history)

        self.load_exams()

    def load_exams(self):
        exams = self.exam_model.list_exams()
        self.table.setRowCount(len(exams))

        for row_idx, e in enumerate(exams):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(e["id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(e["data"])))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(e.get("trimestre", "1º Trimestre"))))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(e.get("tipo_prova", "Prova Regular"))))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(e["nome"])))
            
            full_b_name = str(e.get("bloco_nome") or "-")
            if full_b_name and full_b_name != "-":
                b_parts = [p.strip() for p in full_b_name.split(",") if p.strip()]
                siglas_str = ", ".join(get_acronym(p) for p in b_parts)
            else:
                siglas_str = "-"

            item_bloco = QTableWidgetItem(siglas_str)
            item_bloco.setToolTip(f"Bloco(s): {full_b_name}")
            self.table.setItem(row_idx, 5, item_bloco)
            
            modelos_str = ", ".join(e.get("gabaritos", {}).keys())
            self.table.setItem(row_idx, 6, QTableWidgetItem(modelos_str))

            redacao_str = "Sim" if e.get("possui_redacao") else "Não"
            item_red = QTableWidgetItem(redacao_str)
            item_red.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 7, item_red)

            self.table.setItem(row_idx, 8, QTableWidgetItem(str(e.get("total_processados", 0))))

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

            btn_clone = QPushButton("Clonar")
            btn_clone.setIcon(qta.icon('fa5s.clone', color='#242D64'))
            btn_clone.setObjectName("btnSecondary")
            btn_clone.setMinimumWidth(85)
            btn_clone.clicked.connect(lambda _, e_id=e["id"], e_nome=e["nome"]: self.clone_exam(e_id, e_nome))

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
            btn_layout.addWidget(btn_clone)
            btn_layout.addWidget(btn_edit)
            btn_layout.addWidget(btn_del)

            self.table.setCellWidget(row_idx, 9, btn_panel)

    def new_exam(self):
        dlg = ExamFormDialog(self.exam_model, self.subject_model, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Sucesso", "Prova cadastrada com sucesso!")
            self.load_exams()

    def edit_exam(self, exam_data):
        full_exam = self.exam_model.get_exam_by_id(exam_data["id"])
        dlg = ExamFormDialog(self.exam_model, self.subject_model, self, exam_data=full_exam)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Sucesso", "Prova atualizada com sucesso!")
            self.load_exams()

    def clone_exam(self, exam_id: int, exam_nome: str):
        reply = QMessageBox.question(
            self, "Confirmar Clonagem",
            f"Deseja criar um clone da prova '{exam_nome}'?\n\n"
            f"Uma nova prova chamada '{exam_nome} (CLONE)' será criada com a data de hoje e sem resultados associados.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                new_id = self.exam_model.clone_exam(exam_id)
                self.load_exams()
                QMessageBox.information(self, "Sucesso", f"Prova '{exam_nome}' clonada com sucesso!\nNovo ID: {new_id}")
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Clonar Prova", str(e))

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
