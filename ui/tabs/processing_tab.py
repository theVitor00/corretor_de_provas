import os
import qtawesome as qta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QFileDialog,
    QDialog, QFormLayout, QMessageBox, QGroupBox, QProgressBar,
    QRadioButton, QButtonGroup, QScrollArea, QStyledItemDelegate, QAbstractItemDelegate
)
from PyQt6.QtCore import Qt, QEvent
from models.exam import ExamModel
from models.student import StudentModel
from models.processing import ProcessingModel
from services.dat_parser import DatParser
from services.grading_engine import GradingEngine

class DuplicateStudentDialog(QDialog):
    """
    Diálogo para resolução de duplicatas de matrículas de alunos detectadas no arquivo .DAT
    """
    def __init__(self, matricula: str, duplicate_items: list, parent=None):
        super().__init__(parent)
        self.matricula = matricula
        self.duplicate_items = duplicate_items
        self.selected_item = duplicate_items[0]
        self.setWindowTitle(f"Duplicata Detectada - Matrícula {matricula}")
        self.setWindowIcon(qta.icon('fa5s.copy', color='#EF4444'))
        self.resize(640, 320)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        info_lbl = QLabel(
            f"<b>Atenção: Duplicata de Aluno no Arquivo de Respostas!</b><br>"
            f"A matrícula <b>'{self.matricula}'</b> foi encontrada <b>{len(self.duplicate_items)} vezes</b> no arquivo enviado.<br>"
            "Escolha qual ocorrência deseja <b>MANTER</b>. A(s) outra(s) será(ão) descartada(s)."
        )
        info_lbl.setWordWrap(True)
        layout.addWidget(info_lbl)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Seleção", "Linha #", "Tipo Prova", "Respostas Registradas"])
        table.verticalHeader().setDefaultSectionSize(32)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        table.setRowCount(len(self.duplicate_items))
        self.button_group = QButtonGroup(self)

        for row_idx, item in enumerate(self.duplicate_items):
            rb = QRadioButton(f"Manter Linha {item['line_number']}")
            if row_idx == 0:
                rb.setChecked(True)
            self.button_group.addButton(rb, row_idx)

            table.setCellWidget(row_idx, 0, rb)
            table.setItem(row_idx, 1, QTableWidgetItem(f"Linha {item['line_number']}"))
            table.setItem(row_idx, 2, QTableWidgetItem(f"Tipo {item['tipo']}"))
            table.setItem(row_idx, 3, QTableWidgetItem(item['respostas']))

        layout.addWidget(table)

        btn_box = QHBoxLayout()
        btn_confirm = QPushButton("Confirmar Escolha e Excluir Duplicata")
        btn_confirm.setIcon(qta.icon('fa5s.check', color='white'))
        btn_confirm.setObjectName("btnNavy")
        btn_confirm.clicked.connect(self.accept_choice)

        btn_box.addStretch()
        btn_box.addWidget(btn_confirm)
        layout.addLayout(btn_box)

    def accept_choice(self):
        selected_idx = self.button_group.checkedId()
        if selected_idx >= 0 and selected_idx < len(self.duplicate_items):
            self.selected_item = self.duplicate_items[selected_idx]
        self.accept()


class HeaderFixDialog(QDialog):
    """
    Diálogo para correção manual de dados de aluno e matrícula não encontrada.
    """
    def __init__(self, raw_item: dict, known_types: list, student_model: StudentModel = None, parent=None):
        super().__init__(parent)
        self.raw_item = raw_item
        self.known_types = known_types
        self.student_model = student_model or StudentModel()
        self.setWindowTitle(f"Corrigir Matrícula Não Encontrada - Matrícula {raw_item.get('matricula', '')}")
        self.setWindowIcon(qta.icon('fa5s.user-edit', color='#EF4444'))
        self.resize(520, 320)
        self.aluno_id = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        info_lbl = QLabel(
            f"<b>Erro de Processamento: Matrícula Não Encontrada</b><br>"
            f"A matrícula <b>'{self.raw_item.get('matricula', '')}'</b> não consta no cadastro de alunos.<br>"
            "Você pode corrigir a matrícula para vincular a um aluno existente ou preencher o Nome e a Turma para cadastrar o novo aluno."
        )
        info_lbl.setWordWrap(True)
        layout.addWidget(info_lbl)

        form = QFormLayout()

        self.lbl_respostas = QLabel(f"<code>{self.raw_item.get('respostas', '')}</code>")
        self.txt_matricula = QLineEdit(str(self.raw_item.get("matricula", "")))
        self.txt_nome = QLineEdit()

        self.combo_turma = QComboBox()
        self.combo_turma.setEditable(True)
        turmas_existentes = self.student_model.list_turmas()
        if not turmas_existentes:
            turmas_existentes = ["1ª Série", "2ª Série", "3ª Série"]
        for t in turmas_existentes:
            self.combo_turma.addItem(t)

        self.combo_tipo = QComboBox()
        for t in self.known_types:
            self.combo_tipo.addItem(f"Tipo {t}", str(t))

        idx = self.combo_tipo.findData(str(self.raw_item.get("tipo", "1")))
        if idx < 0:
            raw_t_digits = "".join(ch for ch in str(self.raw_item.get("tipo", "")) if ch.isdigit())
            if raw_t_digits:
                for i in range(self.combo_tipo.count()):
                    item_data_digits = "".join(ch for ch in str(self.combo_tipo.itemData(i)) if ch.isdigit())
                    if item_data_digits == raw_t_digits:
                        idx = i
                        break
        if idx >= 0:
            self.combo_tipo.setCurrentIndex(idx)

        self.lbl_status_search = QLabel("")
        self.lbl_status_search.setWordWrap(True)

        form.addRow("Respostas Registradas:", self.lbl_respostas)
        form.addRow("Matrícula do Aluno *:", self.txt_matricula)
        form.addRow("Nome do Aluno:", self.txt_nome)
        form.addRow("Turma:", self.combo_turma)
        form.addRow("Tipo de Prova:", self.combo_tipo)
        form.addRow("", self.lbl_status_search)

        layout.addLayout(form)

        self.txt_matricula.textChanged.connect(self.on_matricula_changed)
        self.on_matricula_changed()

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setIcon(qta.icon('fa5s.times', color='#242D64'))
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Salvar e Processar Prova")
        btn_save.setIcon(qta.icon('fa5s.check', color='white'))
        btn_save.setObjectName("btnNavy")
        btn_save.clicked.connect(self.validate_and_accept)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def on_matricula_changed(self):
        mat = clean_matricula(self.txt_matricula.text())
        if not mat:
            self.lbl_status_search.setText("<font color='gray'>Digite o número da matrícula.</font>")
            self.aluno_id = None
            return

        st = self.student_model.get_by_matricula(mat)
        if st:
            self.aluno_id = st["id"]
            self.txt_nome.setText(st["nome"])
            idx_t = self.combo_turma.findText(st["turma"])
            if idx_t >= 0:
                self.combo_turma.setCurrentIndex(idx_t)
            else:
                self.combo_turma.setCurrentText(st["turma"])
            self.lbl_status_search.setText(f"<font color='#059669'><b>Aluno Cadastrado Encontrado:</b> {st['nome']} ({st['turma']})</font>")
        else:
            self.aluno_id = None
            self.lbl_status_search.setText("<font color='#D97706'><b>Matrícula não cadastrada.</b> Preencha Nome e Turma para cadastrar o aluno.</font>")

    def validate_and_accept(self):
        mat = clean_matricula(self.txt_matricula.text())
        if not mat:
            QMessageBox.warning(self, "Aviso", "Informe uma matrícula válida para o aluno.")
            return

        st = self.student_model.get_by_matricula(mat)
        if st:
            self.aluno_id = st["id"]
        else:
            nome = self.txt_nome.text().strip()
            turma = self.combo_turma.currentText().strip()
            if not nome or not turma:
                QMessageBox.warning(
                    self, "Preenchimento Obrigatório",
                    f"A matrícula '{mat}' não está cadastrada.\nPreencha os campos Nome e Turma para cadastrar o aluno no sistema."
                )
                return
            try:
                self.aluno_id = self.student_model.create(mat, nome, turma)
            except Exception as e:
                QMessageBox.critical(self, "Erro no Cadastro", f"Erro ao cadastrar aluno:\n{str(e)}")
                return

        self.accept()

    def get_fixed_data(self):
        return {
            "matricula": clean_matricula(self.txt_matricula.text()),
            "aluno_id": self.aluno_id,
            "tipo": self.combo_tipo.currentData()
        }


import csv
from database import clean_matricula

class EnterNextRowDelegate(QStyledItemDelegate):
    """
    Delegate para capturar a tecla Enter/Return ao finalizar a edição de uma célula,
    aplicar estilo de editor centralizado com padding e mover a seleção automaticamente para a linha seguinte (estilo Excel).
    """
    def __init__(self, table_widget: QTableWidget, parent=None):
        super().__init__(parent)
        self.table_widget = table_widget

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        if isinstance(editor, QLineEdit):
            editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
            editor.setStyleSheet("""
                QLineEdit {
                    background-color: #FFFFFF;
                    border: 2px solid #242D64;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-weight: bold;
                    font-size: 13px;
                }
            """)
        return editor

    def eventFilter(self, editor, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.commitData.emit(editor)
                self.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.NoHint)
                
                curr_row = self.table_widget.currentRow()
                if curr_row < self.table_widget.rowCount() - 1:
                    next_row = curr_row + 1
                    self.table_widget.setCurrentCell(next_row, 2)
                    next_item = self.table_widget.item(next_row, 2)
                    if next_item:
                        self.table_widget.editItem(next_item)
                return True
        return super().eventFilter(editor, event)


class ExcelTableWidget(QTableWidget):
    """
    Tabela customizada que avança para a linha seguinte ao pressionar Enter na visualização das células.
    """
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            curr_row = self.currentRow()
            if curr_row < self.rowCount() - 1:
                next_row = curr_row + 1
                self.setCurrentCell(next_row, 2)
                next_item = self.item(next_row, 2)
                if next_item:
                    self.editItem(next_item)
                event.accept()
                return
        super().keyPressEvent(event)


class EssayGradesDialog(QDialog):
    """
    Diálogo para inserção manual e importação em lotes (.csv) de notas de redação.
    """
    def __init__(self, exam: dict, processing_model: ProcessingModel, parent=None):
        super().__init__(parent)
        self.exam = exam
        self.processing_model = processing_model
        self.setWindowTitle(f"Lançamento de Notas de Redação - {exam['nome']}")
        self.setWindowIcon(qta.icon('fa5s.pen-nib', color='#242D64'))
        self.resize(620, 520)
        self.results = self.processing_model.list_results_for_exam(exam["id"])
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)

        # Header Info
        info_lbl = QLabel(
            f"<b>Prova:</b> {self.exam['nome']} | <b>Data:</b> {self.exam['data']}<br>"
            "Insira manualmente as notas de redação dos alunos na coluna <b>Nota</b> ou importe em lotes via arquivo CSV.<br>"
            "<i>Nota: Notações decimais com ponto (ex: 19.5) e vírgula (ex: 19,5) são aceitas igualmente. Ao pressionar Enter, o cursor avança para o próximo aluno.</i>"
        )
        info_lbl.setWordWrap(True)
        layout.addWidget(info_lbl)

        # Action Bar (Import CSV)
        h_tools = QHBoxLayout()
        btn_csv = QPushButton("Enviar em Lotes (.csv)")
        btn_csv.setIcon(qta.icon('fa5s.file-csv', color='white'))
        btn_csv.setObjectName("btnNavy")
        btn_csv.clicked.connect(self.import_csv)

        h_tools.addWidget(btn_csv)
        h_tools.addStretch()
        layout.addLayout(h_tools)

        # Label de grupo Redação
        gb_redacao = QGroupBox("Redação")
        gb_layout = QVBoxLayout(gb_redacao)
        gb_layout.setContentsMargins(20, 10, 20, 10)

        # Tabela com as três colunas solicitadas: Matrícula, Nome, Nota (com navegação estilo Excel por Enter)
        self.tbl_grades = ExcelTableWidget()
        self.delegate = EnterNextRowDelegate(self.tbl_grades, self)
        self.tbl_grades.setItemDelegateForColumn(2, self.delegate)

        self.tbl_grades.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_grades.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        self.tbl_grades.setStyleSheet("""
            QTableWidget {
                gridline-color: #CBD5E1;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background-color: #DBEAFE;
                color: #1E293B;
                font-weight: bold;
            }
        """)

        self.tbl_grades.setColumnCount(3)
        self.tbl_grades.setHorizontalHeaderLabels(["Matrícula", "Nome", "Nota"])
        self.tbl_grades.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_grades.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_grades.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.tbl_grades.setColumnWidth(2, 160)

        self.tbl_grades.setRowCount(len(self.results))
        for row_idx, r in enumerate(self.results):
            # Matrícula (read-only)
            item_mat = QTableWidgetItem(str(r["aluno_matricula"]))
            item_mat.setFlags(item_mat.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_mat.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl_grades.setItem(row_idx, 0, item_mat)

            # Nome (read-only)
            item_nome = QTableWidgetItem(str(r["aluno_nome"]))
            item_nome.setFlags(item_nome.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tbl_grades.setItem(row_idx, 1, item_nome)

            # Nota (editable)
            n_red = r.get("nota_redacao")
            if n_red is not None:
                n_str = f"{n_red:.2f}".replace(".", ",")
            else:
                n_str = ""

            item_nota = QTableWidgetItem(n_str)
            item_nota.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl_grades.setItem(row_idx, 2, item_nota)

        gb_layout.addWidget(self.tbl_grades)
        layout.addWidget(gb_redacao)

        # Footer Actions
        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setIcon(qta.icon('fa5s.times', color='#242D64'))
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Salvar Notas de Redação")
        btn_save.setIcon(qta.icon('fa5s.save', color='white'))
        btn_save.setObjectName("btnNavy")
        btn_save.clicked.connect(self.save_grades)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def import_csv(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo CSV de Redação", "", "Arquivos CSV (*.csv);;Todos os Arquivos (*.*)"
        )
        if not filepath:
            return

        imported_count = 0
        errors = []

        try:
            with open(filepath, mode="r", encoding="utf-8-sig", errors="ignore") as f:
                first_line = f.readline()
                f.seek(0)
                delimiter = ";" if ";" in first_line and "," not in first_line else ","
                reader = csv.reader(f, delimiter=delimiter)

                mat_to_row = {}
                for row_idx in range(self.tbl_grades.rowCount()):
                    mat = clean_matricula(self.tbl_grades.item(row_idx, 0).text())
                    mat_to_row[mat] = row_idx

                for line_idx, cols in enumerate(reader, start=1):
                    if not cols or len(cols) < 2:
                        continue

                    raw_mat = cols[0].strip()
                    raw_nota = cols[1].strip()

                    if line_idx == 1 and not raw_mat.isdigit() and ("matr" in raw_mat.lower() or "nota" in raw_nota.lower()):
                        continue

                    mat_cleaned = clean_matricula(raw_mat)
                    if mat_cleaned in mat_to_row:
                        row_target = mat_to_row[mat_cleaned]
                        try:
                            nota_val = self.parse_grade_val(raw_nota)
                            nota_formatted = f"{nota_val:.2f}".replace(".", ",")
                            self.tbl_grades.item(row_target, 2).setText(nota_formatted)
                            imported_count += 1
                        except ValueError:
                            errors.append(f"Linha {line_idx}: nota inválida '{raw_nota}' para a matrícula '{raw_mat}'")
                    else:
                        errors.append(f"Linha {line_idx}: matrícula '{raw_mat}' não encontrada nos alunos desta prova")

            msg = f"{imported_count} nota(s) de redação importada(s) do CSV com sucesso!"
            if errors:
                msg += f"\n\nAvisos ({len(errors)}):\n" + "\n".join(errors[:5])
                if len(errors) > 5:
                    msg += f"\n... e mais {len(errors) - 5} avisos."
                QMessageBox.warning(self, "Resultado da Importação CSV", msg)
            else:
                QMessageBox.information(self, "Sucesso", msg)

        except Exception as e:
            QMessageBox.critical(self, "Erro na Leitura do CSV", f"Erro ao ler arquivo CSV:\n{str(e)}")

    def parse_grade_val(self, text: str) -> float:
        if text is None:
            raise ValueError("Vazio")
        s = str(text).strip().replace(",", ".")
        if not s:
            raise ValueError("Vazio")
        val = float(s)
        if val < 0:
            raise ValueError("Nota negativa")
        return val

    def save_grades(self):
        grades_dict = {}
        for r in range(self.tbl_grades.rowCount()):
            mat = self.tbl_grades.item(r, 0).text()
            cell_nota = self.tbl_grades.item(r, 2)
            nota_text = cell_nota.text().strip() if cell_nota else ""

            if not nota_text:
                grades_dict[mat] = None
            else:
                try:
                    val = self.parse_grade_val(nota_text)
                    grades_dict[mat] = val
                except ValueError:
                    QMessageBox.warning(
                        self, "Nota Inválida",
                        f"A nota '{nota_text}' inserida para a matrícula {mat} é inválida."
                    )
                    self.tbl_grades.setCurrentCell(r, 2)
                    return

        try:
            self.processing_model.update_essay_grades(self.exam["id"], grades_dict)
            QMessageBox.information(self, "Sucesso", "Notas de redação salvas com sucesso no banco de dados!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar", f"Erro ao salvar notas no banco de dados:\n{str(e)}")


class ProcessingTab(QWidget):
    def __init__(self, on_view_results_request=None, parent=None):
        super().__init__(parent)
        self.exam_model = ExamModel()
        self.student_model = StudentModel()
        self.processing_model = ProcessingModel()
        self.on_view_results_request = on_view_results_request
        self.selected_exam_id = None
        self.dat_file_paths = {} # {parte_num: filepath}
        self.partes_config = [] # list of partes
        self.file_input_widgets = {} # {parte_num: (QLineEdit, QPushButton)}
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        # Exam & Multi-File Selection Group
        self.gb_select = QGroupBox("1. Seleção da Prova e Arquivo(s) .DAT de Respostas")
        self.f_select = QFormLayout(self.gb_select)

        self.combo_exam = QComboBox()
        self.combo_exam.currentIndexChanged.connect(self.on_exam_changed)
        self.f_select.addRow("Selecione a Prova *:", self.combo_exam)

        self.layout_file_inputs = QVBoxLayout()
        self.f_select.addRow(self.layout_file_inputs)

        layout.addWidget(self.gb_select)

        # Processing Actions & Progress
        gb_process = QGroupBox("2. Processamento e Validação do Controle 000")
        l_process = QVBoxLayout(gb_process)

        h_btn_proc = QHBoxLayout()
        self.btn_process = QPushButton("Processar Prova e Calcular Notas")
        self.btn_process.setIcon(qta.icon('fa5s.bolt', color='white'))
        self.btn_process.setObjectName("btnNavy")
        self.btn_process.clicked.connect(self.process_dat_file)
        h_btn_proc.addWidget(self.btn_process)

        self.btn_essay_grades = QPushButton("Enviar Notas de Redação")
        self.btn_essay_grades.setIcon(qta.icon('fa5s.pen-nib', color='#242D64'))
        self.btn_essay_grades.setObjectName("btnSecondary")
        self.btn_essay_grades.setEnabled(False)
        self.btn_essay_grades.setToolTip("Insira as notas de redação dos alunos após a leitura do arquivo de respostas .DAT")
        self.btn_essay_grades.clicked.connect(self.open_essay_grades)
        h_btn_proc.addWidget(self.btn_essay_grades)

        self.btn_view_res = QPushButton("Ir Para Conferência / Resultados")
        self.btn_view_res.setIcon(qta.icon('fa5s.chart-pie', color='#242D64'))
        self.btn_view_res.setObjectName("btnSecondary")
        self.btn_view_res.setEnabled(False)
        self.btn_view_res.clicked.connect(self.go_to_results)
        h_btn_proc.addWidget(self.btn_view_res)

        l_process.addLayout(h_btn_proc)

        self.lbl_status = QLabel("Aguardando arquivo(s) para processamento...")
        l_process.addWidget(self.lbl_status)

        layout.addWidget(gb_process)

        # Table of Control Errors / Warnings
        gb_errors = QGroupBox("Revisão de Erros - Matrículas Não Encontradas no Banco de Dados")
        l_errors = QVBoxLayout(gb_errors)

        self.tbl_errors = QTableWidget()
        self.tbl_errors.setColumnCount(6)
        self.tbl_errors.setHorizontalHeaderLabels([
            "Linha #", "Matrícula", "Tipo Prova", "Respostas Registradas", "Erro Reportado", "Ação"
        ])
        self.tbl_errors.verticalHeader().setDefaultSectionSize(32)
        self.tbl_errors.setMaximumHeight(180)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.tbl_errors.setColumnWidth(5, 140)

        l_errors.addWidget(self.tbl_errors)
        layout.addWidget(gb_errors)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        self.load_exams_combo()

    def load_exams_combo(self):
        self.combo_exam.blockSignals(True)
        self.combo_exam.clear()
        self.combo_exam.addItem("Selecione uma prova...", None)

        exams = self.exam_model.list_exams()
        for e in exams:
            self.combo_exam.addItem(f"{e['nome']} ({e['data']})", e["id"])

        self.combo_exam.blockSignals(False)

    def select_exam(self, exam_id: int):
        self.load_exams_combo()
        idx = self.combo_exam.findData(exam_id)
        if idx >= 0:
            self.combo_exam.setCurrentIndex(idx)

    def on_exam_changed(self):
        self.selected_exam_id = self.combo_exam.currentData()
        self.btn_view_res.setEnabled(False)
        self.btn_essay_grades.setEnabled(False)
        self.dat_file_paths.clear()
        self.file_input_widgets.clear()
        self.clear_file_input_layout()

        if not self.selected_exam_id:
            return

        exam = self.exam_model.get_exam_by_id(self.selected_exam_id)
        if not exam:
            return

        if exam.get("possui_redacao"):
            results = self.processing_model.list_results_for_exam(self.selected_exam_id)
            if results:
                self.btn_essay_grades.setEnabled(True)
                self.btn_view_res.setEnabled(True)
        else:
            results = self.processing_model.list_results_for_exam(self.selected_exam_id)
            if results:
                self.btn_view_res.setEnabled(True)

        partes = exam.get("layout_config", {}).get("partes", [])
        if not partes:
            tot_q = exam.get("num_questoes", 45)
            partes = [{"parte_num": 1, "nome": "Parte Única", "num_questoes": tot_q, "q_start": 1, "q_end": tot_q}]

        self.partes_config = partes

        # Gerar dinamicamente seletores de arquivo por parte
        for p in self.partes_config:
            p_num = p["parte_num"]
            p_nome = p["nome"]
            q_st = p["q_start"]
            q_ed = p["q_end"]

            lbl = QLabel(f"<b>Arquivo .DAT - {p_nome} (Q{q_st} a Q{q_ed}):</b>")
            txt = QLineEdit()
            txt.setReadOnly(True)
            txt.setPlaceholderText(f"Selecione o arquivo .dat para {p_nome}...")

            btn = QPushButton("Buscar Arquivo .DAT...")
            btn.setIcon(qta.icon('fa5s.folder-open', color='white'))
            btn.setObjectName("btnNavy")
            btn.clicked.connect(lambda _, pn=p_num: self.browse_dat_file_for_part(pn))

            h = QHBoxLayout()
            h.addWidget(txt)
            h.addWidget(btn)

            row_w = QWidget()
            vl = QVBoxLayout(row_w)
            vl.setContentsMargins(0, 2, 0, 4)
            vl.addWidget(lbl)
            vl.addLayout(h)

            self.layout_file_inputs.addWidget(row_w)
            self.file_input_widgets[p_num] = (txt, btn)

    def clear_file_input_layout(self):
        while self.layout_file_inputs.count():
            item = self.layout_file_inputs.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def browse_dat_file_for_part(self, parte_num: int):
        filepath, _ = QFileDialog.getOpenFileName(
            self, f"Selecionar Arquivo .DAT para Parte {parte_num}", "", "Arquivos DAT (*.dat);;Todos os Arquivos (*.*)"
        )
        if filepath:
            self.dat_file_paths[parte_num] = filepath
            if parte_num in self.file_input_widgets:
                self.file_input_widgets[parte_num][0].setText(filepath)
            self.lbl_status.setText(f"Arquivo Parte {parte_num} selecionado: {os.path.basename(filepath)}")

    def process_dat_file(self):
        if not self.selected_exam_id:
            QMessageBox.warning(self, "Aviso", "Selecione uma prova antes de processar.")
            return

        exam = self.exam_model.get_exam_by_id(self.selected_exam_id)
        if not exam:
            QMessageBox.critical(self, "Erro", "Prova selecionada não foi encontrada.")
            return

        tot_q = exam.get("num_questoes", 0)
        known_types = list(exam.get("gabaritos", {}).keys())

        # Verificar se arquivo foi fornecido para cada parte
        for p in self.partes_config:
            p_num = p["parte_num"]
            p_nome = p["nome"]
            if p_num not in self.dat_file_paths or not os.path.exists(self.dat_file_paths[p_num]):
                QMessageBox.warning(
                    self, "Arquivo Faltando",
                    f"Por favor, selecione o arquivo .DAT para a **{p_nome}** (Parte {p_num})."
                )
                return

        parser = DatParser()
        # Dicionário de respostas por matrícula agrupado por parte: {matricula: {"tipo": str, "parts": {p_num: item_dict}}}
        student_records = {}

        # Parsear cada arquivo .dat por parte
        for p in self.partes_config:
            p_num = p["parte_num"]
            f_path = self.dat_file_paths[p_num]
            try:
                parsed_items = parser.parse_file(f_path)
            except Exception as e:
                QMessageBox.critical(self, "Erro de Leitura", f"Erro ao ler arquivo .dat da Parte {p_num}:\n{str(e)}")
                return

            for item in parsed_items:
                mat = clean_matricula(item["matricula"])
                if not mat:
                    mat = f"SEM_MAT_{item['line_number']}"

                if mat not in student_records:
                    student_records[mat] = {
                        "matricula": mat,
                        "tipo": item["tipo"] or (known_types[0] if known_types else "1"),
                        "parts": {}
                    }

                student_records[mat]["parts"][p_num] = item

        grading_engine = GradingEngine(exam)
        processed_count = 0
        unfound_matricula_errors = []

        self.processing_model.clear_exam_processings(self.selected_exam_id)

        # Unificar e Corrigir os registros dos alunos
        for mat, record in student_records.items():
            tipo_aluno = record["tipo"]
            
            # Montar a string de respostas unificada contínua (Q1..QNn)
            unified_ans = list(" " * tot_q)

            for p in self.partes_config:
                p_num = p["parte_num"]
                q_st = p["q_start"]
                q_ed = p["q_end"]
                p_len = p["num_questoes"]

                if p_num in record["parts"]:
                    raw_part_ans = record["parts"][p_num]["respostas"].upper()[:p_len].ljust(p_len, " ")
                    for idx in range(p_len):
                        pos = q_st - 1 + idx
                        if pos < tot_q:
                            unified_ans[pos] = raw_part_ans[idx]

            full_respostas_str = "".join(unified_ans)

            # Verificar se aluno existe no banco de dados
            student = self.student_model.get_by_matricula(mat)

            try:
                res = grading_engine.grade_student(tipo_aluno, full_respostas_str)
                if student:
                    self.processing_model.save_processing(
                        prova_id=self.selected_exam_id,
                        aluno_matricula=mat,
                        tipo_prova=tipo_aluno,
                        respostas_aluno=full_respostas_str,
                        status_controle="OK",
                        nota_final=res["nota_final"],
                        percentual_acertos=res["percentual_acertos"],
                        total_acertos=res["total_acertos"],
                        total_questoes=res["total_questoes"],
                        detalhes_disciplinas=res["detalhes_disciplinas"],
                        aluno_id=student["id"]
                    )
                    processed_count += 1
                else:
                    # Matrícula não encontrada no banco de dados -> Reportar erro
                    self.processing_model.save_processing(
                        prova_id=self.selected_exam_id,
                        aluno_matricula=mat,
                        tipo_prova=tipo_aluno,
                        respostas_aluno=full_respostas_str,
                        status_controle="MATRICULA_NAO_ENCONTRADA",
                        nota_final=res["nota_final"],
                        percentual_acertos=res["percentual_acertos"],
                        total_acertos=res["total_acertos"],
                        total_questoes=res["total_questoes"],
                        detalhes_disciplinas=res["detalhes_disciplinas"],
                        aluno_id=None
                    )
                    first_part_item = record["parts"].get(1, list(record["parts"].values())[0]) if record["parts"] else {}
                    line_no = first_part_item.get("line_number", "-")
                    unfound_matricula_errors.append({
                        "line_number": line_no,
                        "raw_line": first_part_item.get("raw_line", f"Matrícula {mat}"),
                        "matricula": mat,
                        "tipo": tipo_aluno,
                        "respostas": full_respostas_str,
                        "error_msg": "Matrícula não encontrada no banco de dados"
                    })
            except Exception as e:
                unfound_matricula_errors.append({
                    "line_number": 0,
                    "raw_line": f"Matrícula {mat}",
                    "matricula": mat,
                    "tipo": tipo_aluno,
                    "respostas": full_respostas_str,
                    "error_msg": str(e)
                })

        self.populate_error_table(unfound_matricula_errors, exam, known_types)

        msg = f"Processamento concluído!\n\nAlunos com matrícula vinculada: {processed_count}\n"
        if unfound_matricula_errors:
            msg += f"Aviso: Matrículas não encontradas no banco de dados: {len(unfound_matricula_errors)}\nReveja os itens na tabela abaixo para vincular ou cadastrar os alunos."
        else:
            msg += "Todas as matrículas foram identificadas e validadas no banco de dados!"

        QMessageBox.information(self, "Resultado do Processamento", msg)
        self.lbl_status.setText(f"Processamento concluído: {processed_count} ok, {len(unfound_matricula_errors)} matrícula(s) pendente(s).")
        self.btn_view_res.setEnabled(True)
        if exam.get("possui_redacao"):
            self.btn_essay_grades.setEnabled(True)

    def open_essay_grades(self):
        if not self.selected_exam_id:
            QMessageBox.warning(self, "Aviso", "Selecione uma prova antes de lançar notas de redação.")
            return
        exam = self.exam_model.get_exam_by_id(self.selected_exam_id)
        if not exam:
            return
        if not exam.get("possui_redacao"):
            QMessageBox.information(self, "Aviso", "Esta prova não foi cadastrada com a opção de redação.")
            return

        dlg = EssayGradesDialog(exam, self.processing_model, parent=self)
        dlg.exec()

    def populate_error_table(self, error_items: list, exam: dict, known_types: list):
        self.tbl_errors.setRowCount(len(error_items))

        for row_idx, item in enumerate(error_items):
            self.tbl_errors.setItem(row_idx, 0, QTableWidgetItem(str(item.get("line_number", "-"))))
            self.tbl_errors.setItem(row_idx, 1, QTableWidgetItem(str(item.get("matricula", ""))))
            self.tbl_errors.setItem(row_idx, 2, QTableWidgetItem(f"Tipo {item.get('tipo', '')}"))
            self.tbl_errors.setItem(row_idx, 3, QTableWidgetItem(item.get("respostas", "")))
            
            err_item = QTableWidgetItem(item.get("error_msg", "Matrícula Não Encontrada"))
            err_item.setForeground(Qt.GlobalColor.red)
            self.tbl_errors.setItem(row_idx, 4, err_item)

            btn_fix = QPushButton("Corrigir Dados")
            btn_fix.setIcon(qta.icon('fa5s.wrench', color='white'))
            btn_fix.setObjectName("btnNavy")
            btn_fix.setMinimumWidth(120)
            btn_fix.clicked.connect(lambda _, it=item: self.fix_header_item(it, exam, known_types))
            self.tbl_errors.setCellWidget(row_idx, 5, btn_fix)

    def fix_header_item(self, item: dict, exam: dict, known_types: list):
        dlg = HeaderFixDialog(item, known_types, student_model=self.student_model, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            fixed_data = dlg.get_fixed_data()
            grading_engine = GradingEngine(exam)

            try:
                res = grading_engine.grade_student(fixed_data["tipo"], item.get("respostas", ""))
                self.processing_model.save_processing(
                    prova_id=self.selected_exam_id,
                    aluno_matricula=fixed_data["matricula"],
                    tipo_prova=fixed_data["tipo"],
                    respostas_aluno=item.get("respostas", ""),
                    status_controle="OK",
                    nota_final=res["nota_final"],
                    percentual_acertos=res["percentual_acertos"],
                    total_acertos=res["total_acertos"],
                    total_questoes=res["total_questoes"],
                    detalhes_disciplinas=res["detalhes_disciplinas"],
                    aluno_id=fixed_data["aluno_id"]
                )
                QMessageBox.information(self, "Sucesso", "Dados do aluno atualizados e nota salva com sucesso!")
                self.process_dat_file()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao aplicar correção:\n{str(e)}")

    def go_to_results(self):
        if self.on_view_results_request and self.selected_exam_id:
            self.on_view_results_request(self.selected_exam_id)

