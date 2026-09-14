import os
import qtawesome as qta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QFileDialog,
    QDialog, QFormLayout, QMessageBox, QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt
from models.exam import ExamModel
from models.student import StudentModel
from models.processing import ProcessingModel
from services.dat_parser import DatParser
from services.grading_engine import GradingEngine

class HeaderFixDialog(QDialog):
    """
    Diálogo para correção manual de dados de cabeçalho (quando aluno[0..2] != 000 ou há inconsistências)
    """
    def __init__(self, raw_item: dict, known_types: list, parent=None):
        super().__init__(parent)
        self.raw_item = raw_item
        self.known_types = known_types
        self.setWindowTitle(f"Revisar Linha {raw_item['line_number']} - Código de Controle Inválido")
        self.setWindowIcon(qta.icon('fa5s.exclamation-triangle', color='#EF4444'))
        self.resize(440, 240)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        info_lbl = QLabel(
            f"<b>Aviso de Leitura:</b> O código de controle inicial de 3 dígitos lido foi <b>'{self.raw_item['control']}'</b> (Esperado '000').\n"
            "Por favor, ajuste manualmente os dados obrigatórios para garantir a leitura correta."
        )
        info_lbl.setWordWrap(True)
        layout.addWidget(info_lbl)

        form = QFormLayout()
        self.txt_control = QLineEdit(self.raw_item["control"])
        self.txt_matricula = QLineEdit(self.raw_item["matricula"])

        self.combo_tipo = QComboBox()
        for t in self.known_types:
            self.combo_tipo.addItem(f"Tipo {t}", t)
        
        idx = self.combo_tipo.findData(self.raw_item["tipo"])
        if idx >= 0:
            self.combo_tipo.setCurrentIndex(idx)

        self.lbl_raw = QLabel(f"<b>Linha Original:</b> <code>{self.raw_item['raw_line']}</code>")

        form.addRow("Linha Bruta:", self.lbl_raw)
        form.addRow("Código de Controle (3 dígitos):", self.txt_control)
        form.addRow("Matrícula do Aluno:", self.txt_matricula)
        form.addRow("Tipo de Prova:", self.combo_tipo)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar / Ignorar Linha")
        btn_cancel.setIcon(qta.icon('fa5s.times', color='#242D64'))
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Confirmar Correção")
        btn_save.setIcon(qta.icon('fa5s.check', color='white'))
        btn_save.setObjectName("btnNavy")
        btn_save.clicked.connect(self.validate_and_accept)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def validate_and_accept(self):
        if not self.txt_matricula.text().strip():
            QMessageBox.warning(self, "Aviso", "Informe uma matrícula válida para o aluno.")
            return
        self.accept()

    def get_fixed_data(self):
        return {
            "control": self.txt_control.text().strip(),
            "matricula": self.txt_matricula.text().strip(),
            "tipo": self.combo_tipo.currentData()
        }


class ProcessingTab(QWidget):
    def __init__(self, on_view_results_request=None, parent=None):
        super().__init__(parent)
        self.exam_model = ExamModel()
        self.student_model = StudentModel()
        self.processing_model = ProcessingModel()
        self.on_view_results_request = on_view_results_request
        self.selected_exam_id = None
        self.dat_filepath = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Exam & File Selection Group
        gb_select = QGroupBox("1. Seleção da Prova e Arquivo .DAT de Respostas")
        f_select = QFormLayout(gb_select)

        self.combo_exam = QComboBox()
        self.combo_exam.currentIndexChanged.connect(self.on_exam_changed)

        h_file = QHBoxLayout()
        self.txt_filepath = QLineEdit()
        self.txt_filepath.setReadOnly(True)
        self.txt_filepath.setPlaceholderText("Nenhum arquivo .dat selecionado...")

        btn_browse = QPushButton("Buscar Arquivo .DAT...")
        btn_browse.setIcon(qta.icon('fa5s.folder-open', color='white'))
        btn_browse.setObjectName("btnNavy")
        btn_browse.clicked.connect(self.browse_dat_file)

        h_file.addWidget(self.txt_filepath)
        h_file.addWidget(btn_browse)

        f_select.addRow("Selecione a Prova *:", self.combo_exam)
        f_select.addRow("Arquivo de Respostas (.dat) *:", h_file)

        layout.addWidget(gb_select)

        # Processing Actions & Progress
        gb_process = QGroupBox("2. Processamento e Validação do Controle 000")
        l_process = QVBoxLayout(gb_process)

        h_btn_proc = QHBoxLayout()
        self.btn_process = QPushButton("Processar Prova e Calcular Notas")
        self.btn_process.setIcon(qta.icon('fa5s.bolt', color='white'))
        self.btn_process.setObjectName("btnNavy")
        self.btn_process.clicked.connect(self.process_dat_file)
        h_btn_proc.addWidget(self.btn_process)

        self.btn_view_res = QPushButton("Ir Para Conferência / Resultados")
        self.btn_view_res.setIcon(qta.icon('fa5s.chart-pie', color='#242D64'))
        self.btn_view_res.setObjectName("btnSecondary")
        self.btn_view_res.setEnabled(False)
        self.btn_view_res.clicked.connect(self.go_to_results)
        h_btn_proc.addWidget(self.btn_view_res)

        l_process.addLayout(h_btn_proc)

        self.lbl_status = QLabel("Aguardando arquivo para processamento...")
        l_process.addWidget(self.lbl_status)

        layout.addWidget(gb_process)

        # Table of Control Errors / Warnings requiring manual review
        gb_errors = QGroupBox("Revisão de Erros de Cabeçalho (Linhas onde aluno[0..2] != 000)")
        l_errors = QVBoxLayout(gb_errors)

        self.tbl_errors = QTableWidget()
        self.tbl_errors.setColumnCount(6)
        self.tbl_errors.setHorizontalHeaderLabels([
            "Linha", "Linha Bruta", "Controle Lido", "Matrícula", "Tipo", "Ação"
        ])
        self.tbl_errors.verticalHeader().setDefaultSectionSize(44)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.tbl_errors.setColumnWidth(5, 150)

        l_errors.addWidget(self.tbl_errors)
        layout.addWidget(gb_errors)

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

    def browse_dat_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo .DAT de Respostas", "", "Arquivos DAT (*.dat);;Todos os Arquivos (*.*)"
        )
        if filepath:
            self.dat_filepath = filepath
            self.txt_filepath.setText(filepath)
            self.lbl_status.setText(f"Arquivo selecionado: {os.path.basename(filepath)}")

    def process_dat_file(self):
        if not self.selected_exam_id:
            QMessageBox.warning(self, "Aviso", "Selecione uma prova antes de processar.")
            return

        if not self.dat_filepath or not os.path.exists(self.dat_filepath):
            QMessageBox.warning(self, "Aviso", "Selecione um arquivo .dat válido.")
            return

        exam = self.exam_model.get_exam_by_id(self.selected_exam_id)
        if not exam:
            QMessageBox.critical(self, "Erro", "Prova selecionada não foi encontrada.")
            return

        known_types = list(exam.get("gabaritos", {}).keys())

        # Ler arquivo .dat
        parser = DatParser()
        try:
            parsed_items = parser.parse_file(self.dat_filepath)
        except Exception as e:
            QMessageBox.critical(self, "Erro de Leitura", f"Erro ao ler arquivo .dat:\n{str(e)}")
            return

        if not parsed_items:
            QMessageBox.warning(self, "Aviso", "O arquivo .dat selecionado está vazio.")
            return

        grading_engine = GradingEngine(exam)

        processed_count = 0
        control_error_items = []

        self.processing_model.clear_exam_processings(self.selected_exam_id)

        for item in parsed_items:
            if not item["control_ok"]:
                control_error_items.append(item)
                self.processing_model.save_processing(
                    prova_id=self.selected_exam_id,
                    aluno_matricula=item["matricula"] or f"DESCONHECIDO_{item['line_number']}",
                    tipo_prova=item["tipo"] or (known_types[0] if known_types else "1"),
                    respostas_aluno=item["respostas"],
                    status_controle="HEADER_ERROR",
                    nota_final=0.0,
                    percentual_acertos=0.0,
                    total_acertos=0,
                    total_questoes=exam.get("num_questoes", 0),
                    detalhes_disciplinas={}
                )
            else:
                try:
                    res = grading_engine.grade_student(item["tipo"], item["respostas"])
                    self.processing_model.save_processing(
                        prova_id=self.selected_exam_id,
                        aluno_matricula=item["matricula"],
                        tipo_prova=item["tipo"],
                        respostas_aluno=item["respostas"],
                        status_controle="OK",
                        nota_final=res["nota_final"],
                        percentual_acertos=res["percentual_acertos"],
                        total_acertos=res["total_acertos"],
                        total_questoes=res["total_questoes"],
                        detalhes_disciplinas=res["detalhes_disciplinas"]
                    )
                    processed_count += 1
                except Exception as e:
                    item["error_msg"] = str(e)
                    control_error_items.append(item)

        self.populate_error_table(control_error_items, exam, known_types)

        msg = f"Processamento concluído!\n\nAlunos corrigidos com sucesso: {processed_count}\n"
        if control_error_items:
            msg += f"Aviso: Inconsistências de cabeçalho (aluno[0..2] != 000): {len(control_error_items)}\nReveja e corrija os itens sinalizados na tabela abaixo."
        else:
            msg += "Todos os registros de cabeçalho ('000') foram validados com sucesso!"

        QMessageBox.information(self, "Resultado do Processamento", msg)
        self.lbl_status.setText(f"Processamento concluído: {processed_count} ok, {len(control_error_items)} para revisão.")
        self.btn_view_res.setEnabled(True)

    def populate_error_table(self, error_items: list, exam: dict, known_types: list):
        self.tbl_errors.setRowCount(len(error_items))

        for row_idx, item in enumerate(error_items):
            self.tbl_errors.setItem(row_idx, 0, QTableWidgetItem(str(item["line_number"])))
            self.tbl_errors.setItem(row_idx, 1, QTableWidgetItem(item["raw_line"]))
            
            c_item = QTableWidgetItem(item["control"])
            c_item.setForeground(Qt.GlobalColor.red)
            self.tbl_errors.setItem(row_idx, 2, c_item)
            
            self.tbl_errors.setItem(row_idx, 3, QTableWidgetItem(item["matricula"]))
            self.tbl_errors.setItem(row_idx, 4, QTableWidgetItem(item["tipo"]))

            btn_fix = QPushButton("Corrigir Dados")
            btn_fix.setIcon(qta.icon('fa5s.wrench', color='white'))
            btn_fix.setObjectName("btnNavy")
            btn_fix.setMinimumWidth(130)
            btn_fix.clicked.connect(lambda _, it=item: self.fix_header_item(it, exam, known_types))
            self.tbl_errors.setCellWidget(row_idx, 5, btn_fix)

    def fix_header_item(self, item: dict, exam: dict, known_types: list):
        dlg = HeaderFixDialog(item, known_types, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            fixed_data = dlg.get_fixed_data()
            grading_engine = GradingEngine(exam)

            try:
                res = grading_engine.grade_student(fixed_data["tipo"], item["respostas"])
                self.processing_model.save_processing(
                    prova_id=self.selected_exam_id,
                    aluno_matricula=fixed_data["matricula"],
                    tipo_prova=fixed_data["tipo"],
                    respostas_aluno=item["respostas"],
                    status_controle="OK",
                    nota_final=res["nota_final"],
                    percentual_acertos=res["percentual_acertos"],
                    total_acertos=res["total_acertos"],
                    total_questoes=res["total_questoes"],
                    detalhes_disciplinas=res["detalhes_disciplinas"]
                )
                QMessageBox.information(self, "Sucesso", "Correção aplicada e nota recalculada!")
                self.process_dat_file()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao aplicar correção:\n{str(e)}")

    def go_to_results(self):
        if self.on_view_results_request and self.selected_exam_id:
            self.on_view_results_request(self.selected_exam_id)
